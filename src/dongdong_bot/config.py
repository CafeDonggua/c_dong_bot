from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

ENV_PATH = "/data/data/com.termux/files/home/storage/shared/program/python/tg_bot/c_dong_bot/.env"
MEMORY_DIR = "/data/data/com.termux/files/home/storage/shared/C_Dong_bot"
DEFAULT_MODEL = "gpt-5-mini"


@dataclass(frozen=True)
class Config:
    openai_api_key: str
    telegram_bot_token: str
    memory_dir: str = MEMORY_DIR
    model: str = DEFAULT_MODEL
    base_max_iters: int = 3
    max_iters_cap: int = 6
    no_progress_limit: int = 3
    json_retry_limit: int = 1


def load_config() -> Config:
    load_dotenv(ENV_PATH)
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    if not openai_api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY，請確認 .env 絕對路徑設定")
    if not telegram_bot_token:
        raise RuntimeError("缺少 TELEGRAM_BOT_TOKEN，請確認 .env 絕對路徑設定")

    Path(MEMORY_DIR).mkdir(parents=True, exist_ok=True)

    return Config(
        openai_api_key=openai_api_key,
        telegram_bot_token=telegram_bot_token,
    )
