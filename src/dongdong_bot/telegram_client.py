from __future__ import annotations

import asyncio
from typing import Callable

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters


class TelegramClient:
    def __init__(self, token: str) -> None:
        self.app = Application.builder().token(token).build()

    def start(self, on_text: Callable[[str], object]) -> None:
        async def _handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not update.message or not update.message.text:
                return
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, on_text, update.message.text)
            reply_text = getattr(response, "reply", str(response))
            await update.message.reply_text(reply_text)

        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle))
        self.app.run_polling(close_loop=False)
