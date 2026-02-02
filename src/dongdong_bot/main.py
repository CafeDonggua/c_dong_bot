from __future__ import annotations

import time

from openai import OpenAI

from dongdong_bot.config import load_config
from dongdong_bot.goap import GoapEngine
from dongdong_bot.lib.embedding_client import EmbeddingClient
from dongdong_bot.lib.intent_classifier import IntentClassifier, IntentExample
from dongdong_bot.lib.search_client import SearchClient
from dongdong_bot.lib.search_formatter import SearchFormatter
from dongdong_bot.lib.nl_search_topic import NLSearchTopicExtractor
from dongdong_bot.lib.report_writer import ReportWriter
from dongdong_bot.memory_store import MemoryStore
from dongdong_bot.monitoring import Monitoring
from dongdong_bot.telegram_client import TelegramClient


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
        return "搜尋失敗，請稍後再試或調整關鍵字。"


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
        return "連結摘要失敗，請確認網址可存取後再試。"


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
    intent_classifier = IntentClassifier(
        embedding_client,
        examples=[
            IntentExample("memory_save", "記住我喜歡手沖咖啡"),
            IntentExample("memory_save", "請記下我的外套是淺藍"),
            IntentExample("memory_save", "幫我記住我的生日是 8 月 10 日"),
            IntentExample("memory_save", "我想要你記住我喜歡無糖拿鐵"),
            IntentExample("memory_query", "我喜歡什麼咖啡"),
            IntentExample("memory_query", "我剛剛讓你記住了什麼"),
            IntentExample("memory_query", "我之前說過什麼喜好"),
            IntentExample("memory_query", "我的外套是什麼顏色"),
            IntentExample("memory_query", "我有什麼需要記住的事情"),
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
    telegram = TelegramClient(config.telegram_bot_token, monitoring, perf_log=config.perf_log)

    def handle_text(text: str):
        start_time = time.perf_counter()
        if text.startswith("/search"):
            return _handle_search_command(text, search_client, search_formatter, monitoring)
        if text.startswith("/summary"):
            return _handle_summary_command(text, search_client, search_formatter, monitoring)
        plan = nl_topic.extract(text)
        if plan.is_search and plan.topic:
            try:
                response = search_client.search_keyword(plan.topic)
                if plan.wants_report:
                    if response.is_empty():
                        return "找不到相關結果，無法產出案例文件。"
                    report_path = report_writer.write(
                        title=plan.topic,
                        summary=response.summary or "（無摘要）",
                        bullets=response.bullets or ["（無重點）"],
                        sources=response.sources or ["（無來源）"],
                    )
                    memory_store.log_report(plan.topic, report_path)
                    return f"已完成案例整理，檔案：{report_path}"
                return search_formatter.format(response)
            except Exception as exc:
                monitoring.error(exc)
                return "搜尋失敗，請稍後再試或調整關鍵字。"
        response = goap.respond(text)
        if config.perf_log:
            goap_ms = (time.perf_counter() - start_time) * 1000
            monitoring.perf("handle_text.goap", goap_ms, f"decision={response.decision}")
        if response.memory_content:
            mem_start = time.perf_counter()
            try:
                embedding = embedding_client.embed(response.memory_content)
                memory_store.save_with_embedding(response.memory_content, embedding)
            except Exception:
                memory_store.save(response.memory_content)
            if config.perf_log:
                mem_ms = (time.perf_counter() - mem_start) * 1000
                monitoring.perf("memory.save", mem_ms)
            response.reply = f"{response.reply}\n\n已為你記住：{response.memory_content}"
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
                joined = "\n".join(f"- {item}" for item in results)
                response.reply = f"找到的記憶：\n{joined}"
            else:
                response.reply = "找不到相關記憶。"
        if config.perf_log:
            total_ms = (time.perf_counter() - start_time) * 1000
            monitoring.perf("handle_text.total", total_ms)
        return response

    telegram.start(handle_text)


if __name__ == "__main__":
    main()
