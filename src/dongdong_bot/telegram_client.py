from __future__ import annotations

import asyncio
import time
from typing import Callable

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from dongdong_bot.monitoring import Monitoring


class TelegramClient:
    def __init__(self, token: str, monitoring: Monitoring, perf_log: bool = False) -> None:
        self.monitoring = monitoring
        self.perf_log = perf_log
        self.app = Application.builder().token(token).post_init(self._post_init).build()

    def start(self, on_text: Callable[[str], object]) -> None:
        async def _handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not update.message or not update.message.text:
                return
            self.monitoring.received()
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, on_text, update.message.text)
            reply_text = getattr(response, "reply", str(response))
            send_start = time.perf_counter()
            await update.message.reply_text(reply_text)
            if self.perf_log:
                send_ms = (time.perf_counter() - send_start) * 1000
                print(f"[perf] telegram.reply ms={send_ms:.1f}")
            self.monitoring.replied()

        async def _handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not update.message or not update.message.text:
                return
            self.monitoring.received()
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, on_text, update.message.text)
            reply_text = getattr(response, "reply", str(response))
            send_start = time.perf_counter()
            await update.message.reply_text(reply_text)
            if self.perf_log:
                send_ms = (time.perf_counter() - send_start) * 1000
                print(f"[perf] telegram.reply ms={send_ms:.1f}")
            self.monitoring.replied()

        async def _heartbeat(_: ContextTypes.DEFAULT_TYPE) -> None:
            self.monitoring.heartbeat()

        async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
            if context.error:
                self.monitoring.error(context.error)

        self.app.add_handler(CommandHandler("search", _handle_command))
        self.app.add_handler(CommandHandler("summary", _handle_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle))
        self.app.add_error_handler(_error_handler)
        self.app.job_queue.run_repeating(
            _heartbeat,
            interval=self.monitoring.heartbeat_interval_seconds,
            first=self.monitoring.heartbeat_interval_seconds,
        )
        self.app.run_polling(close_loop=False)

    async def _post_init(self, _: Application) -> None:
        self.monitoring.startup()
