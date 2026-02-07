from __future__ import annotations

import time
from datetime import datetime
import json
from pathlib import Path

from openai import NotFoundError, OpenAI, PermissionDeniedError

from dongdong_bot.agent.allowlist_store import AllowlistEntry, AllowlistStore
from dongdong_bot.agent.capability_catalog import CapabilityCatalog
from dongdong_bot.agent.intent_router import IntentRouter
from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleCommand, ScheduleParser
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.agent.skills import SkillRegistry
from dongdong_bot.agent.session import SessionStore
from dongdong_bot.agent.loop import GoapEngine
from dongdong_bot.agent.memory import MemoryStore, is_short_term_query, search_session_messages
from dongdong_bot.channels.telegram import IncomingMessage, TelegramClient
from dongdong_bot.config import load_config
from dongdong_bot.cron.scheduler import ReminderScheduler
from dongdong_bot.lib.embedding_client import EmbeddingClient
from dongdong_bot.lib.intent_classifier import IntentClassifier, IntentExample
from dongdong_bot.lib.search_client import SearchClient
from dongdong_bot.lib.search_formatter import SearchFormatter
from dongdong_bot.lib.nl_search_topic import NLSearchTopicExtractor
from dongdong_bot.lib.report_content import normalize_report_content
from dongdong_bot.lib.report_writer import ReportWriter
from dongdong_bot.lib.response_style import ResponseStyler
from dongdong_bot.monitoring import Monitoring
from dongdong_bot.lib.vector_math import cosine_similarity, top_k_scored


SKILL_MEMORY_SAVE = "memory-save"
SKILL_MEMORY_RECALL = "memory-recall"
SKILL_SEARCH_REPORT = "nl-search-report"
DECISION_LABELS = {
    "schedule_add": "行程提醒",
    "schedule_list": "行程查詢",
    "memory_save": "記憶保存",
    "memory_query": "記憶回想",
    "search_report": "搜尋整理",
    "direct_reply": "一般回覆",
}


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


def _handle_skill_command(text: str, registry: SkillRegistry) -> str:
    parts = text.strip().split()
    if len(parts) == 1 or parts[1] == "list":
        skills = registry.list_skills()
        if not skills:
            return "目前沒有技能清單。"
        lines = [
            f"- {skill.name}: {'啟用' if skill.enabled else '停用'}"
            for skill in skills
        ]
        return "技能清單：\n" + "\n".join(lines)
    if len(parts) >= 3 and parts[1] in {"enable", "disable"}:
        target = parts[2]
        enabled = parts[1] == "enable"
        registry.set_enabled(target, enabled)
        return f"技能 {target} 已{'啟用' if enabled else '停用'}。"
    return "用法：/skill list | /skill enable <name> | /skill disable <name>"


def _handle_allowlist_command(text: str, store: AllowlistStore) -> str:
    parts = text.strip().split()
    if len(parts) == 1 or parts[1] == "list":
        entries = store.list_entries()
        if not entries:
            return "允許名單目前為空。"
        lines = [f"- {entry.user_id} ({entry.channel_type})" for entry in entries]
        return "允許名單：\n" + "\n".join(lines)
    if len(parts) >= 3 and parts[1] in {"add", "remove"}:
        user_id = parts[2]
        channel = parts[3] if len(parts) >= 4 else "telegram"
        if parts[1] == "add":
            store.add(AllowlistEntry(user_id=user_id, channel_type=channel))
            return f"已加入允許名單：{user_id} ({channel})"
        store.remove(user_id, channel)
        return f"已移除允許名單：{user_id} ({channel})"
    return "用法：/allowlist list | /allowlist add <user_id> [channel] | /allowlist remove <user_id> [channel]"


def _append_decision_note(reply: str, capability: str) -> str:
    label = DECISION_LABELS.get(capability, "一般回覆")
    return f"【{label}】{reply}"


def _parse_json_object(raw: str) -> dict | None:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = raw[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _parse_json_list(raw: str) -> list[str] | None:
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = raw[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, list):
        return None
    cleaned = []
    for item in parsed:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def _extract_schedule_from_llm(
    llm_client: OpenAIClient,
    model: str,
    user_text: str,
    now: datetime,
) -> ScheduleCommand | None:
    prompt = (
        "你是行程資訊擷取器，請從使用者輸入中提取行程時間與內容。\n"
        "請只輸出單行 JSON，欄位包含: datetime, title。\n"
        "datetime 格式為 YYYY-MM-DD HH:MM（24 小時制），若無法判斷請輸出空字串。\n"
        "title 為行程內容的精簡描述，若無法判斷可輸出空字串。\n"
        f"目前時間: {now.strftime('%Y-%m-%d %H:%M')}\n"
        f"使用者輸入: {user_text}\n"
    )
    raw = llm_client.generate(model=model, prompt=prompt)
    parsed = _parse_json_object(raw.strip()) if raw else None
    if not parsed:
        return None
    dt_raw = str(parsed.get("datetime", "") or "").strip()
    title = str(parsed.get("title", "") or "").strip()
    if not dt_raw:
        return None
    try:
        start_time = datetime.strptime(dt_raw, "%Y-%m-%d %H:%M")
    except ValueError:
        return None
    if not title:
        title = "行程"
    return ScheduleCommand(action="add", title=title, start_time=start_time)


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


def _focus_memory_query(
    llm_client: OpenAIClient,
    model: str,
    text: str,
) -> str:
    prompt = (
        "你是記憶檢索的查詢重寫器。\n"
        "請將使用者問題改寫成可用於查找記憶的精簡短語，"
        "保留關鍵主題/人物/時間/物品，移除多餘語氣。\n"
        "只輸出短語，不要解釋或加標點；無法改寫就原樣輸出。\n\n"
        f"使用者問題: {text}\n"
    )
    raw = llm_client.generate(model=model, prompt=prompt).strip()
    cleaned = raw.strip().strip("「」\"'`")
    return cleaned or text.strip()


def _summarize_memory_hits(
    llm_client: OpenAIClient,
    model: str,
    question: str,
    results: list[str],
    max_items: int = 5,
) -> list[str] | None:
    if not results:
        return []
    prompt = (
        "你是記憶回想整理助手。\n"
        "根據使用者問題，從記憶清單挑選最相關的 1-3 條，必要時合併重複內容。\n"
        "只輸出 JSON 陣列，例如 [\"...\", \"...\"]，若沒有相關內容輸出 []。\n\n"
        f"使用者問題: {question}\n"
        "記憶清單:\n"
        + "\n".join(f"- {item}" for item in results)
        + "\n"
    )
    raw = llm_client.generate(model=model, prompt=prompt).strip()
    parsed = _parse_json_list(raw)
    if parsed is None:
        return None
    if not parsed:
        return []
    return parsed[:max_items]


def _resolve_memory_content(
    user_text: str,
    response,
    llm_client: OpenAIClient,
    model: str,
    explicit_save: bool,
) -> tuple[str | None, bool]:
    if not explicit_save:
        return None, False
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
    if is_short_term_query(text):
        return True, "short_term", 0
    if intent_classifier is not None:
        intent, score = intent_classifier.classify(text)
        if intent == "memory_query":
            return True, f"intent_score:{score:.2f}", 0
    if not _has_memory_keywords(text):
        return False, "no_hint", 0
    try:
        results, source = _semantic_memory_fallback(
            text, embedding_client, memory_store, min_score=min_score
        )
    except Exception:
        return True, "keyword", 0
    return True, source if results else "keyword", len(results)


def _is_explicit_memory_save(text: str) -> bool:
    keywords = ("記住", "記下", "備忘", "記得")
    return any(keyword in text for keyword in keywords)


def _has_memory_keywords(text: str) -> bool:
    keywords = (
        "記憶",
        "回想",
        "回憶",
        "記得",
        "之前",
        "上次",
        "曾經",
        "喜歡",
        "喝什麼",
        "吃什麼",
        "行程",
        "安排",
        "待辦",
    )
    return any(keyword in text for keyword in keywords)


def _preference_keyword_terms(text: str) -> list[str]:
    if "喜歡" in text:
        return ["喜歡"]
    terms: list[str] = []
    if "喝什麼" in text or "喝啥" in text:
        terms.append("喝")
    if "吃什麼" in text or "吃啥" in text:
        terms.append("吃")
    return terms


def _keyword_memory_fallback(query: str, memory_store: MemoryStore) -> list[str]:
    terms = _preference_keyword_terms(query)
    if not terms:
        return []
    candidates = memory_store.recent_entries(days=90, max_entries=200)
    hits = [item for item in candidates if any(term in item for term in terms)]
    if not hits:
        return []
    deduped = []
    seen = set()
    for item in hits:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _coerce_message(payload: IncomingMessage | str) -> tuple[str, str, str, str]:
    if isinstance(payload, IncomingMessage):
        text = payload.text
        user_id = payload.user_id or "default"
        chat_id = payload.chat_id or user_id
        channel = payload.channel
        return text, user_id, chat_id, channel
    return str(payload), "local", "local", "local"


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
    schedule_store = ScheduleStore(config.schedules_path)
    reminder_store = ReminderStore(config.reminders_path)
    schedule_parser = ScheduleParser()
    schedule_service = ScheduleService(schedule_store, reminder_store)
    scheduler = ReminderScheduler(schedule_store, reminder_store)
    session_store = SessionStore()
    skills_dir = Path(__file__).resolve().parents[2] / "resources" / "skills"
    skill_registry = SkillRegistry(
        skills_dir=str(skills_dir),
        state_path=config.skills_state_path,
    )
    allowlist_store = AllowlistStore(config.allowlist_path)
    capability_catalog = CapabilityCatalog(config.capabilities_path)
    intent_router = IntentRouter(
        generate=llm_client.generate,
        model=config.fast_model,
        catalog=capability_catalog,
    )

    monitoring.info(
        f"memory_dir={memory_store.memory_dir} reports_dir={memory_store.reports_dir}"
    )

    def handle_message(payload: IncomingMessage | str):
        start_time = time.perf_counter()
        text, user_id, chat_id, channel = _coerce_message(payload)
        session_store.touch(user_id, text)

        if text.startswith("/skill"):
            return _handle_skill_command(text, skill_registry)
        if text.startswith("/allowlist"):
            return _handle_allowlist_command(text, allowlist_store)

        if text.startswith("/search"):
            if not skill_registry.is_enabled(SKILL_SEARCH_REPORT):
                return "搜尋整理技能已停用。"
            return _handle_search_command(text, search_client, search_formatter, monitoring)
        if text.startswith("/summary"):
            if not skill_registry.is_enabled(SKILL_SEARCH_REPORT):
                return "搜尋整理技能已停用。"
            return _handle_summary_command(text, search_client, search_formatter, monitoring)

        decision = intent_router.route(text)
        monitoring.info(
            "router_decision="
            f"{decision.capability} missing={decision.missing_inputs} "
            f"clarify={decision.needs_clarification} confidence={decision.confidence:.2f}"
        )
        should_clarify = decision.needs_clarification
        if decision.capability in {"memory_query", "schedule_list"} and text.strip():
            should_clarify = False

        if decision.capability == "schedule_add":
            command = schedule_parser.parse(text)
            if command and command.action == "add" and command.start_time:
                result = schedule_service.handle(command, user_id, chat_id)
                return _append_decision_note(result.reply, decision.capability)
            llm_command = _extract_schedule_from_llm(
                llm_client=llm_client,
                model=config.fast_model,
                user_text=text,
                now=datetime.now(),
            )
            if llm_command:
                result = schedule_service.handle(llm_command, user_id, chat_id)
                return _append_decision_note(result.reply, decision.capability)
            return _append_decision_note(
                intent_router.build_clarification_question(decision),
                decision.capability,
            )

        if decision.capability == "schedule_list":
            list_command = schedule_parser.parse(text)
            if not list_command or list_command.action != "list":
                list_command = ScheduleCommand(action="list", title="")
            result = schedule_service.handle(list_command, user_id, chat_id)
            return _append_decision_note(result.reply, decision.capability)

        if decision.capability == "search_report":
            if not skill_registry.is_enabled(SKILL_SEARCH_REPORT):
                return _append_decision_note("搜尋整理技能已停用。", decision.capability)
            plan = nl_topic.extract(text)
            topic = plan.topic.strip() if plan.topic else ""
            url = plan.url.strip() if plan.url else ""
            if not topic and not url:
                topic = text.strip()
            if not topic and not url:
                return _append_decision_note(
                    intent_router.build_clarification_question(decision),
                    decision.capability,
                )
            try:
                if url:
                    response = search_client.summarize_link(url)
                else:
                    response = search_client.search_keyword(topic)
                if plan.wants_report:
                    title = topic or url
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
                    return _append_decision_note(
                        f"已完成案例整理，檔案：{report_path}",
                        decision.capability,
                    )
                return _append_decision_note(
                    search_formatter.format(response),
                    decision.capability,
                )
            except Exception as exc:
                monitoring.error(exc)
                return _append_decision_note(
                    _format_search_error(exc, search_formatter),
                    decision.capability,
                )

        if should_clarify:
            return _append_decision_note(
                intent_router.build_clarification_question(decision),
                decision.capability,
            )

        forced_decision = None
        if decision.capability in {"memory_save", "memory_query", "direct_reply"}:
            forced_decision = decision.capability
        response = goap.respond(
            text,
            forced_decision=forced_decision,
            forced_reason=decision.reason,
        )
        if response.decision == "memory_save" and not skill_registry.is_enabled(SKILL_MEMORY_SAVE):
            response.reply = "記憶保存技能已停用。"
            response.memory_content = None
            response.decision = "direct_reply"
        if response.decision == "memory_query" and not skill_registry.is_enabled(SKILL_MEMORY_RECALL):
            response.reply = "記憶回想技能已停用。"
            response.memory_query = None
            response.decision = "direct_reply"

        monitoring.info(
            "goap_decision="
            f"{response.decision} memory_query={bool(response.memory_query)}"
            f" memory_content={bool(response.memory_content)}"
        )
        if response.decision in {"direct_reply", "goap"} and not response.memory_query:
            styled = response_styler.style(response.reply, text)
            response.reply = styled.reply
        if config.perf_log:
            goap_ms = (time.perf_counter() - start_time) * 1000
            monitoring.perf("handle_text.goap", goap_ms, f"decision={response.decision}")
        resolved_memory, normalized = (None, False)
        if skill_registry.is_enabled(SKILL_MEMORY_SAVE):
            explicit_save = _is_explicit_memory_save(text) or decision.capability == "memory_save"
            resolved_memory, normalized = _resolve_memory_content(
                text, response, llm_client, config.fast_model, explicit_save
            )
            if response.decision == "memory_save" and not resolved_memory:
                response.reply = "如果要我記住內容，請說「請記住：...」"
                response.decision = "direct_reply"
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
            schedule_command = schedule_parser.parse(text)
            if schedule_command and schedule_command.action == "add" and schedule_command.start_time:
                schedule_result = schedule_service.handle(schedule_command, user_id, chat_id)
                response.reply = f"{response.reply}\n\n{schedule_result.reply}"
            elif (
                schedule_parser.is_schedule_hint(text)
                and schedule_parser.has_date_hint(text)
                and not schedule_parser.has_time_hint(text)
            ):
                response.reply = (
                    f"{response.reply}\n\n"
                    "若要加入行程，請告訴我時間，例如：明天 10:00 開會。"
                )
        if response.memory_query:
            if not skill_registry.is_enabled(SKILL_MEMORY_RECALL):
                response.reply = "記憶回想技能已停用。"
                response.memory_query = None
            else:
                query_text = response.memory_query.strip()
                session = session_store.get(user_id)
                if session and is_short_term_query(response.memory_query):
                    session_messages = session.messages[:-1] if len(session.messages) > 1 else []
                    session_hits = search_session_messages(
                        session_messages, response.memory_query
                    )
                    if session_hits:
                        joined = "\n".join(f"- {item}" for item in session_hits)
                        response.reply = f"最近對話（未保存）：\n{joined}"
                        return response
                    monitoring.info("session_memory hit=0")
                focus_query = query_text
                try:
                    focus_query = _focus_memory_query(
                        llm_client, config.fast_model, query_text
                    )
                    if focus_query and focus_query != query_text:
                        monitoring.info(f"memory_focus={focus_query}")
                except Exception:
                    monitoring.info("memory_focus_failed=1")
                results = []
                try:
                    query_start = time.perf_counter()
                    embedding = None
                    try:
                        embedding = embedding_client.embed(focus_query)
                    except Exception:
                        monitoring.info("memory_embed_failed=1")
                        if focus_query != query_text:
                            try:
                                embedding = embedding_client.embed(query_text)
                            except Exception:
                                monitoring.info("memory_embed_failed=1 original=1")
                    if embedding is not None:
                        semantic_hits = memory_store.semantic_search(embedding)
                        semantic_hits = memory_store.filter_by_score(semantic_hits)
                        if semantic_hits:
                            results = [item for item, _score in semantic_hits]
                    if not results:
                        if response.memory_date_range:
                            start = response.memory_date_range.get("start")
                            end = response.memory_date_range.get("end")
                            if start and end:
                                results = memory_store.query_range(focus_query, start, end)
                        elif response.memory_date:
                            results = memory_store.query(focus_query, date=response.memory_date)
                        else:
                            results = memory_store.query(focus_query)
                        if not results and focus_query != query_text:
                            if response.memory_date_range:
                                start = response.memory_date_range.get("start")
                                end = response.memory_date_range.get("end")
                                if start and end:
                                    results = memory_store.query_range(query_text, start, end)
                            elif response.memory_date:
                                results = memory_store.query(query_text, date=response.memory_date)
                            else:
                                results = memory_store.query(query_text)
                        if not results:
                            try:
                                semantic_hits, source = _semantic_memory_fallback(
                                    focus_query,
                                    embedding_client,
                                    memory_store,
                                )
                                if semantic_hits:
                                    results = semantic_hits
                                    monitoring.info(f"memory_fallback={source}")
                            except Exception:
                                monitoring.info("memory_fallback_failed=1")
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
                    candidates = memory_store.summarize_results(
                        results, max_items=10, max_chars=160
                    )
                    summarized = None
                    try:
                        summarized = _summarize_memory_hits(
                            llm_client,
                            config.fast_model,
                            query_text,
                            candidates,
                            max_items=5,
                        )
                    except Exception:
                        monitoring.info("memory_summarize_failed=1")
                    if summarized is None:
                        summarized = memory_store.summarize_results(results)
                    if summarized:
                        joined = "\n".join(f"- {item}" for item in summarized)
                        response.reply = f"找到的記憶：\n{joined}"
                    else:
                        response.reply = "找不到相關記憶。你可以告訴我想記住的內容，我幫你記下。"
                else:
                    response.reply = "找不到相關記憶。你可以告訴我想記住的內容，我幫你記下。"
        if config.perf_log:
            total_ms = (time.perf_counter() - start_time) * 1000
            monitoring.perf("handle_text.total", total_ms)
        response.reply = _append_decision_note(response.reply, decision.capability)
        return response

    def allowlist_checker(message: IncomingMessage) -> bool:
        return allowlist_store.is_allowed(message.user_id, message.channel)

    telegram = TelegramClient(
        config.telegram_bot_token,
        monitoring,
        perf_log=config.perf_log,
        allowlist_checker=allowlist_checker,
        scheduler=scheduler,
    )
    telegram.start(handle_message)


if __name__ == "__main__":
    main()
