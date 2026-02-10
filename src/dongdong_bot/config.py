from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

ENV_PATH = "/data/data/com.termux/files/home/storage/shared/program/python/tg_bot/c_dong_bot/.env"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = str(PROJECT_ROOT / "data")
DEFAULT_MODEL = "gpt-5-mini"
FAST_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
SEARCH_MODEL = "gpt-4o-mini"
EMBEDDING_INDEX_FILENAME = "embeddings.jsonl"
INTENT_CACHE_FILENAME = "intent_index.json"
ALLOWLIST_FILENAME = "allowlist.json"
SCHEDULES_FILENAME = "schedules.json"
REMINDERS_FILENAME = "reminders.json"
SKILLS_STATE_FILENAME = "skills_state.json"
CAPABILITIES_FILENAME = "capabilities.yaml"
MEMORY_SUBDIR = "memory"
REPORTS_SUBDIR = "reports"
HEARTBEAT_INTERVAL_SECONDS = 30 * 60
ERROR_THROTTLE_SECONDS = 60
MEMORY_QUALITY_ACCURACY_THRESHOLD = 0.6
MEMORY_QUALITY_RELEVANCE_THRESHOLD = 0.5
MEMORY_QUALITY_DUPLICATE_RATE_MAX = 0.2
PERF_LOG_ENV = "PERF_LOG"
EMBEDDING_KEY_ENV = "OPENAI_EMBEDDING_KEY"
SEARCH_KEY_ENV = "OPENAI_SEARCH_API_KEY"
CAPABILITIES_PATH = str(Path(__file__).resolve().parent / "agent" / CAPABILITIES_FILENAME)


@dataclass(frozen=True)
class Config:
    openai_api_key: str
    embedding_api_key: str
    telegram_bot_token: str
    memory_dir: str = MEMORY_DIR
    model: str = DEFAULT_MODEL
    fast_model: str = FAST_MODEL
    embedding_model: str = EMBEDDING_MODEL
    embedding_index_path: str = str(Path(MEMORY_DIR) / EMBEDDING_INDEX_FILENAME)
    intent_cache_path: str = str(Path(MEMORY_DIR) / INTENT_CACHE_FILENAME)
    memory_path: str = str(Path(MEMORY_DIR) / MEMORY_SUBDIR)
    reports_path: str = str(Path(MEMORY_DIR) / REPORTS_SUBDIR)
    allowlist_path: str = str(Path(MEMORY_DIR) / ALLOWLIST_FILENAME)
    schedules_path: str = str(Path(MEMORY_DIR) / SCHEDULES_FILENAME)
    reminders_path: str = str(Path(MEMORY_DIR) / REMINDERS_FILENAME)
    skills_state_path: str = str(Path(MEMORY_DIR) / SKILLS_STATE_FILENAME)
    capabilities_path: str = CAPABILITIES_PATH
    search_api_key: str = ""
    search_model: str = SEARCH_MODEL
    heartbeat_interval_seconds: int = HEARTBEAT_INTERVAL_SECONDS
    error_throttle_seconds: int = ERROR_THROTTLE_SECONDS
    memory_quality_accuracy_threshold: float = MEMORY_QUALITY_ACCURACY_THRESHOLD
    memory_quality_relevance_threshold: float = MEMORY_QUALITY_RELEVANCE_THRESHOLD
    memory_quality_duplicate_rate_max: float = MEMORY_QUALITY_DUPLICATE_RATE_MAX
    perf_log: bool = False
    base_max_iters: int = 3
    max_iters_cap: int = 6
    no_progress_limit: int = 3
    json_retry_limit: int = 1


def load_config() -> Config:
    load_dotenv(ENV_PATH)
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    embedding_api_key = os.getenv(EMBEDDING_KEY_ENV, "").strip()
    search_api_key = os.getenv(SEARCH_KEY_ENV, "").strip()
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    if not openai_api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY，請確認 .env 絕對路徑設定")
    if not embedding_api_key:
        embedding_api_key = openai_api_key
    if not search_api_key:
        search_api_key = openai_api_key
    if not telegram_bot_token:
        raise RuntimeError("缺少 TELEGRAM_BOT_TOKEN，請確認 .env 絕對路徑設定")

    Path(MEMORY_DIR).mkdir(parents=True, exist_ok=True)

    perf_log = os.getenv(PERF_LOG_ENV, "0").strip().lower() in {"1", "true", "yes", "on"}

    return Config(
        openai_api_key=openai_api_key,
        embedding_api_key=embedding_api_key,
        search_api_key=search_api_key,
        telegram_bot_token=telegram_bot_token,
        perf_log=perf_log,
    )
