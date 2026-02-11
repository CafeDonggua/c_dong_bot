from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

from telegram import Update
from telegram.error import Conflict, NetworkError, RetryAfter, TimedOut
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from dongdong_bot.cron.scheduler import ReminderScheduler
from dongdong_bot.monitoring import Monitoring


@dataclass(frozen=True)
class IncomingMessage:
    text: str
    user_id: str
    chat_id: str
    user_name: str
    channel: str = "telegram"


AllowlistChecker = Callable[[IncomingMessage], bool]


class TelegramClient:
    COMMAND_NAMES = ("help", "search", "summary", "skill", "allowlist", "cron")

    def __init__(
        self,
        token: str,
        monitoring: Monitoring,
        perf_log: bool = False,
        allowlist_checker: Optional[AllowlistChecker] = None,
        scheduler: ReminderScheduler | None = None,
        reminder_interval_seconds: int = 60,
    ) -> None:
        self.monitoring = monitoring
        self.perf_log = perf_log
        self.allowlist_checker = allowlist_checker
        self.scheduler = scheduler
        self.reminder_interval_seconds = reminder_interval_seconds
        self.app = Application.builder().token(token).post_init(self._post_init).build()

    def start(self, on_message: Callable[[IncomingMessage], object]) -> None:
        async def _handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not update.message or not update.message.text:
                return
            self.monitoring.received()
            message = self._build_message(update)
            if self.allowlist_checker and not self.allowlist_checker(message):
                await self._send_with_retry(
                    lambda: update.message.reply_text("你尚未被授權使用此服務。")
                )
                return
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, on_message, message)
            reply_text = getattr(response, "reply", str(response))
            send_start = time.perf_counter()
            await self._send_with_retry(lambda: update.message.reply_text(reply_text))
            if self.perf_log:
                send_ms = (time.perf_counter() - send_start) * 1000
                print(f"[perf] telegram.reply ms={send_ms:.1f}")
            self.monitoring.replied()

        async def _handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not update.message or not update.message.text:
                return
            self.monitoring.received()
            message = self._build_message(update)
            if self.allowlist_checker and not self.allowlist_checker(message):
                await self._send_with_retry(
                    lambda: update.message.reply_text("你尚未被授權使用此服務。")
                )
                return
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, on_message, message)
            reply_text = getattr(response, "reply", str(response))
            send_start = time.perf_counter()
            await self._send_with_retry(lambda: update.message.reply_text(reply_text))
            if self.perf_log:
                send_ms = (time.perf_counter() - send_start) * 1000
                print(f"[perf] telegram.reply ms={send_ms:.1f}")
            self.monitoring.replied()

        async def _heartbeat(_: ContextTypes.DEFAULT_TYPE) -> None:
            self.monitoring.heartbeat()

        async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
            if context.error:
                self.monitoring.error(context.error)
                if isinstance(context.error, Conflict):
                    self.monitoring.info("telegram_conflict_hint=duplicate polling process detected")

        async def _reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
            if not self.scheduler:
                return
            due = self.scheduler.collect_due()
            for reminder in due:
                try:
                    await self._send_with_retry(
                        lambda: context.bot.send_message(
                            chat_id=reminder.chat_id,
                            text=reminder.message,
                        )
                    )
                    self.scheduler.mark_sent(reminder)
                except Exception as exc:
                    self.scheduler.mark_failed(reminder, str(exc))

        for command in self.COMMAND_NAMES:
            self.app.add_handler(CommandHandler(command, _handle_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle))
        self.app.add_error_handler(_error_handler)
        self.app.job_queue.run_repeating(
            _heartbeat,
            interval=self.monitoring.heartbeat_interval_seconds,
            first=self.monitoring.heartbeat_interval_seconds,
        )
        if self.scheduler:
            self.app.job_queue.run_repeating(
                _reminder_job,
                interval=self.reminder_interval_seconds,
                first=self.reminder_interval_seconds,
            )
        self.app.run_polling(close_loop=False)

    async def _post_init(self, _: Application) -> None:
        self.monitoring.startup()

    async def _send_with_retry(
        self,
        operation: Callable[[], Awaitable[object]],
        retries: int = 1,
    ) -> None:
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                await operation()
                return
            except (TimedOut, NetworkError, RetryAfter) as exc:
                last_error = exc
                self.monitoring.error(exc)
                if attempt >= retries:
                    break
                delay = 1.0 + attempt
                if isinstance(exc, RetryAfter):
                    delay = max(delay, float(exc.retry_after))
                await asyncio.sleep(delay)
        if last_error:
            raise last_error

    @staticmethod
    def _build_message(update: Update) -> IncomingMessage:
        user = update.effective_user
        chat = update.effective_chat
        user_id = str(user.id) if user else ""
        chat_id = str(chat.id) if chat else user_id
        user_name = user.full_name if user else ""
        text = update.message.text if update.message else ""
        return IncomingMessage(text=text, user_id=user_id, chat_id=chat_id, user_name=user_name)
