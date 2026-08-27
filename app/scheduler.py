import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import Database

logger = logging.getLogger(__name__)


class ReminderScheduler:
    def __init__(self, bot: Bot, db: Database):
        self.bot = bot
        self.db = db
        self.scheduler = AsyncIOScheduler(timezone="UTC")

    async def start(self) -> None:
        # Run frequently and check users according to their own timezone.
        self.scheduler.add_job(
            self._send_due_reminders,
            "interval",
            minutes=1,
            id="daily_reminders",
            replace_existing=True,
            max_instances=1,
        )
        self.scheduler.start()

    async def stop(self) -> None:
        self.scheduler.shutdown(wait=False)

    async def _send_due_reminders(self) -> None:
        # Mongo query is intentionally broad enough to support per-user timezones.
        users = await self.db.db.users.find({"reminder_enabled": True}).to_list(None)

        for user in users:
            try:
                tz = ZoneInfo(user.get("timezone", "UTC"))
                now = datetime.now(tz)
                if now.strftime("%H:%M") != user.get("reminder_time"):
                    continue

                today = now.strftime("%Y-%m-%d")
                if user.get("last_reminder_date") == today:
                    continue

                await self.bot.send_message(
                    user["telegram_id"],
                    "👋 Quick IELTS practice?\n\n"
                    "You only need a minute. Use /topic and send me a voice answer. 🎤",
                )

                await self.db.upsert_user(
                    user["telegram_id"],
                    last_reminder_date=today,
                )
            except Exception:
                logger.exception("Failed to send reminder to user %s", user.get("telegram_id"))
