from __future__ import annotations

import time
from datetime import datetime

from openai import NotFoundError, OpenAI, PermissionDeniedError

from dongdong_bot.config import load_config
from dongdong_bot.goap import GoapEngine
from dongdong_bot.lib.embedding_client import EmbeddingClient
from dongdong_bot.lib.intent_classifier import IntentClassifier, IntentExample
from dongdong_bot.lib.search_client import SearchClient
from dongdong_bot.lib.search_formatter import SearchFormatter
from dongdong_bot.lib.nl_search_topic import NLSearchTopicExtractor
from dongdong_bot.lib.report_content import normalize_report_content
from dongdong_bot.lib.report_writer import ReportWriter
from dongdong_bot.lib.response_style import ResponseStyler
from dongdong_bot.memory_store import MemoryStore
from dongdong_bot.monitoring import Monitoring
from dongdong_bot.telegram_client import TelegramClient
from dongdong_bot.lib.vector_math import cosine_similarity, top_k_scored


class OpenAIClient:
    def __init__(self, api_key: str) -> None:
        self.client = OpenAI(api_key=api_key)

    def generate(self, model: str, prompt: str) -> str:
        response = self.client.responses.create(
            model=model,
            input=[{"role": "user", "content": prompt}],
        )
        return response.output_text


def _handle_search_command(
    text: str,
    search_client: SearchClient,
    formatter: SearchFormatter,
    monitoring: Monitoring | None = None,
) -> str:
    query = text.replace("/search", "", 1).strip()
    if not query:
        return "請提供關鍵字，例如：/search 台灣能源政策"
    try:
        response = search_client.search_keyword(query)
        return formatter.format(response)
    except Exception as exc:
        if monitoring is not None:
            monitoring.error(exc)
        return _format_search_error(exc, formatter)


def _handle_summary_command(
    text: str,
    search_client: SearchClient,
    formatter: SearchFormatter,
    monitoring: Monitoring | None = None,
) -> str:
    url = text.replace("/summary", "", 1).strip()
    if not url:
        return "請提供連結，例如：/summary https://example.com"
    try:
        response = search_client.summarize_link(url)
        return formatter.format(response)
    except Exception as exc:
        if monitoring is not None:
            monitoring.error(exc)
        return _format_search_error(exc, formatter, default_reason="連結摘要失敗")


def _format_search_error(
    exc: Exception,
    formatter: SearchFormatter,
    default_reason: str = "搜尋失敗",
) -> str:
    reason = default_reason
    suggestion = "請稍後再試或改用 /search /summary 指令。"
    if isinstance(exc, (NotFoundError, PermissionDeniedError)):
        reason = "搜尋模型不可用或權限不足"
        suggestion = "請確認 OPENAI_SEARCH_API_KEY 或改用 /search 指令。"
    return formatter.format_error(reason, suggestion)


def _semantic_memory_fallback(
    text: str,
    embedding_client: EmbeddingClient,
    memory_store: MemoryStore,
    min_score: float = 0.25,
) -> tuple[list[str], str]:
    embedding = embedding_client.embed(text)
    semantic_hits = memory_store.semantic_search(embedding, min_score=min_score)
    semantic_hits = memory_store.filter_by_score(semantic_hits)
    if semantic_hits:
        return [item for item, _score in semantic_hits], "embedding_index"

    candidates = memory_store.recent_entries()
    if not candidates:
        return [], "recent_empty"
    scored = []
    for item in candidates:
        try:
            item_vector = embedding_client.embed(item)
        except Exception:
            continue
        score = cosine_similarity(embedding, item_vector)
        if score >= min_score:
            scored.append((item, score))
    if scored:
        return [item for item, _score in top_k_scored(scored, 5)], "recent_semantic"
    return [], "no_match"


def _normalize_memory_fallback(
    llm_client: OpenAIClient,
    model: str,
    text: str,
) -> str:
    prompt = (
        "將使用者輸入改寫成可保存的短記憶，保留重點，不要加解釋。\n"
        "只輸出一句話，不要引號。\n\n"
        f"使用者輸入: {text}\n"
    )
    return llm_client.generate(model=model, prompt=prompt).strip()


def _resolve_memory_content(
    user_text: str,
    response,
    llm_client: OpenAIClient,
    model: str,
) -> tuple[str | None, bool]:
    if response.memory_content:
        return response.memory_content.strip(), False
    if response.decision == "memory_save":
        raw = user_text.strip()
        if not raw:
            return None, False
        try:
            normalized = _normalize_memory_fallback(llm_client, model, raw)
            return normalized or raw, True
        except Exception:
            return raw, True
    return None, False


def _memory_query_hint(
    text: str,
    intent_classifier: IntentClassifier | None,
    embedding_client: EmbeddingClient,
    memory_store: MemoryStore,
    min_score: float = 0.25,
) -> tuple[bool, str, int]:
    if intent_classifier is not None:
        intent, score = intent_classifier.classify(text)
        if intent == "memory_query":
            return True, f"intent_score:{score:.2f}", 0
    try:
        results, source = _semantic_memory_fallback(
            text, embedding_client, memory_store, min_score=min_score
        )
    except Exception:
        return False, "error", 0
    return bool(results), source, len(results)


def main() -> None:
    config = load_config()
    monitoring = Monitoring(
        heartbeat_interval_seconds=config.heartbeat_interval_seconds,
        error_throttle_seconds=config.error_throttle_seconds,
    )
    llm_client = OpenAIClient(config.openai_api_key)
    embedding_client = EmbeddingClient(config.embedding_api_key, config.embedding_model)
    search_client = SearchClient(config.search_api_key, config.search_model)
    search_formatter = SearchFormatter()
    report_writer = ReportWriter(config.reports_path)
    nl_topic = NLSearchTopicExtractor(
        generate=llm_client.generate,
        model=config.fast_model,
    )
    response_styler = ResponseStyler()
    intent_classifier = IntentClassifier(
        embedding_client,
        examples=[
            IntentExample("memory_save", "記住我喜歡手沖咖啡"),
            IntentExample("memory_save", "請記下我的外套是淺藍"),
            IntentExample("memory_save", "幫我記住我的生日是 8 月 10 日"),
            IntentExample("memory_save", "我想要你記住我喜歡無糖拿鐵"),
            IntentExample("memory_save", "幫我記住：後天中午12點剪頭"),
            IntentExample("memory_save", "記住：後天中午12點剪頭"),
            IntentExample("memory_save", "請記住我現在有一支衣索比亞烏拉嘎蘇克的咖啡豆"),
            IntentExample("memory_query", "我喜歡什麼咖啡"),
            IntentExample("memory_query", "我剛剛讓你記住了什麼"),
            IntentExample("memory_query", "我之前說過什麼喜好"),
            IntentExample("memory_query", "我的外套是什麼顏色"),
            IntentExample("memory_query", "我有什麼需要記住的事情"),
            IntentExample("memory_query", "我有什麼咖啡豆"),
            IntentExample("memory_query", "我有什麼排定的行程"),
            IntentExample("memory_query", "我有哪些待辦"),
            IntentExample("memory_query", "我有哪些行程"),
            IntentExample("memory_query", "我的行程是什麼"),
            IntentExample("memory_query", "我最近有什麼行程"),
            IntentExample("memory_query", "我最近有哪些安排"),
            IntentExample("memory_query", "我有什麼安排"),
            IntentExample("memory_query", "我有哪些安排"),
            IntentExample("memory_query", "我最近要做什麼"),
            IntentExample("use_tool", "今天台北天氣如何"),
            IntentExample("use_tool", "現在美元對台幣匯率"),
            IntentExample("use_tool", "今天是幾號"),
            IntentExample("use_tool", "現在洛杉磯是幾點"),
        ],
        cache_path=config.intent_cache_path,
    )
    goap = GoapEngine(
        llm_client=llm_client,
        model=config.model,
        fast_model=config.fast_model,
        intent_classifier=intent_classifier.classify,
        base_max_iters=config.base_max_iters,
        max_iters_cap=config.max_iters_cap,
        no_progress_limit=config.no_progress_limit,
        json_retry_limit=config.json_retry_limit,
        perf_log=config.perf_log,
    )
    memory_store = MemoryStore(
        config.memory_dir,
        embedding_index_path=config.embedding_index_path,
    )
    monitoring.info(
        f"memory_dir={memory_store.memory_dir} reports_dir={memory_store.reports_dir}"
    )
    telegram = TelegramClient(config.telegram_bot_token, monitoring, perf_log=config.perf_log)

    def handle_text(text: str):
        start_time = time.perf_counter()
        if text.startswith("/search"):
            return _handle_search_command(text, search_client, search_formatter, monitoring)
        if text.startswith("/summary"):
            return _handle_summary_command(text, search_client, search_formatter, monitoring)
        plan = nl_topic.extract(text)
        memory_hint, memory_reason, memory_hits = _memory_query_hint(
            text, intent_classifier, embedding_client, memory_store
        )
        if plan.is_search and memory_hint:
            monitoring.info(
                f"memory_hint=1 bypass_search=1 reason={memory_reason} hits={memory_hits}"
            )
        if plan.is_search and (plan.topic or plan.url) and not memory_hint:
            monitoring.info("memory_hint=0 search_path=1")
            try:
                if plan.url:
                    response = search_client.summarize_link(plan.url)
                else:
                    response = search_client.search_keyword(plan.topic)
                if plan.wants_report:
                    title = plan.topic or plan.url
                    normalized = normalize_report_content(
                        response,
                        reason="找不到相關結果或來源內容不足",
                        suggestion="請調整關鍵字、加入時間/地點或改用 /search 指令再試。",
                    )
                    report_path = report_writer.write(
                        title=title,
                        content=normalized,
                        query_text=title,
                        query_time=datetime.now(),
                    )
                    memory_store.log_report(title, report_path)
                    return f"已完成案例整理，檔案：{report_path}"
                return search_formatter.format(response)
            except Exception as exc:
                monitoring.error(exc)
                return _format_search_error(exc, search_formatter)
        response = goap.respond(text)
        monitoring.info(
            "goap_decision="
            f"{response.decision} memory_query={bool(response.memory_query)}"
            f" memory_content={bool(response.memory_content)}"
        )
        if response.decision in {"direct_reply", "goap"} and not response.memory_query:
            monitoring.info(f"memory_fallback attempt decision={response.decision}")
            try:
                semantic_results, source = _semantic_memory_fallback(
                    text, embedding_client, memory_store
                )
            except Exception:
                semantic_results, source = [], "error"
            if semantic_results:
                response.decision = "memory_query"
                response.memory_query = text
                monitoring.info(
                    f"memory_fallback hit=1 source={source} items={len(semantic_results)}"
                )
            else:
                monitoring.info(f"memory_fallback hit=0 source={source}")
        if response.decision in {"direct_reply", "goap"} and not response.memory_query:
            styled = response_styler.style(response.reply, text)
            response.reply = styled.reply
        if config.perf_log:
            goap_ms = (time.perf_counter() - start_time) * 1000
            monitoring.perf("handle_text.goap", goap_ms, f"decision={response.decision}")
        resolved_memory, normalized = _resolve_memory_content(
            text, response, llm_client, config.fast_model
        )
        if resolved_memory:
            if response.decision == "memory_save":
                response.reply = "已記住。"
            mem_start = time.perf_counter()
            try:
                embedding = embedding_client.embed(resolved_memory)
                saved_path = memory_store.save_with_embedding(resolved_memory, embedding)
            except Exception:
                saved_path = memory_store.save(resolved_memory)
            monitoring.info(f"memory_saved path={saved_path}")
            if not response.memory_content:
                monitoring.info("memory_save_fallback=1 source=user_text")
            if normalized:
                monitoring.info("memory_save_normalized=1")
            if config.perf_log:
                mem_ms = (time.perf_counter() - mem_start) * 1000
                monitoring.perf("memory.save", mem_ms)
            response.reply = f"{response.reply}\n\n已為你記住：{resolved_memory}"
        if response.memory_query:
            results = []
            try:
                query_start = time.perf_counter()
                embedding = embedding_client.embed(response.memory_query)
                semantic_hits = memory_store.semantic_search(embedding)
                semantic_hits = memory_store.filter_by_score(semantic_hits)
                if semantic_hits:
                    results = [item for item, _score in semantic_hits]
                else:
                    if response.memory_date_range:
                        start = response.memory_date_range.get("start")
                        end = response.memory_date_range.get("end")
                        if start and end:
                            results = memory_store.query_range(response.memory_query, start, end)
                    elif response.memory_date:
                        results = memory_store.query(response.memory_query, date=response.memory_date)
                    else:
                        results = memory_store.query(response.memory_query)
                if config.perf_log:
                    query_ms = (time.perf_counter() - query_start) * 1000
                    monitoring.perf("memory.query", query_ms)
            except ValueError:
                response.reply = f"{response.reply}\n\n日期格式不正確，請使用 YYYY-MM-DD。"
                return response
            except Exception:
                response.reply = f"{response.reply}\n\n記憶檢索暫時無法使用，請稍後再試。"
                return response
            if results:
                results = memory_store.summarize_results(results)
                joined = "\n".join(f"- {item}" for item in results)
                response.reply = f"找到的記憶：\n{joined}"
            else:
                response.reply = "找不到相關記憶。你可以告訴我想記住的內容，我幫你記下。"
        if config.perf_log:
            total_ms = (time.perf_counter() - start_time) * 1000
            monitoring.perf("handle_text.total", total_ms)
        return response

    telegram.start(handle_text)


if __name__ == "__main__":
    main()
