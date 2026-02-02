from __future__ import annotations

from openai import OpenAI

from dongdong_bot.config import load_config
from dongdong_bot.goap import GoapEngine
from dongdong_bot.memory_store import MemoryStore
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


def main() -> None:
    config = load_config()
    llm_client = OpenAIClient(config.openai_api_key)
    goap = GoapEngine(
        llm_client=llm_client,
        model=config.model,
        base_max_iters=config.base_max_iters,
        max_iters_cap=config.max_iters_cap,
        no_progress_limit=config.no_progress_limit,
        json_retry_limit=config.json_retry_limit,
    )
    memory_store = MemoryStore(config.memory_dir)
    telegram = TelegramClient(config.telegram_bot_token)

    def handle_text(text: str):
        response = goap.respond(text)
        if response.memory_content:
            memory_store.save(response.memory_content)
            response.reply = f"{response.reply}\n\n已為你記住：{response.memory_content}"
        if response.memory_query:
            results = []
            try:
                if response.memory_date_range:
                    start = response.memory_date_range.get("start")
                    end = response.memory_date_range.get("end")
                    if start and end:
                        results = memory_store.query_range(response.memory_query, start, end)
                elif response.memory_date:
                    results = memory_store.query(response.memory_query, date=response.memory_date)
                else:
                    results = memory_store.query(response.memory_query)
            except ValueError:
                response.reply = f"{response.reply}\n\n日期格式不正確，請使用 YYYY-MM-DD。"
                return response
            if results:
                joined = "\n".join(f"- {item}" for item in results)
                response.reply = f"{response.reply}\n\n找到的記憶：\n{joined}"
            else:
                response.reply = f"{response.reply}\n\n找不到相關記憶。"
        return response

    telegram.start(handle_text)


if __name__ == "__main__":
    main()
