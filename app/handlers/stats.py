from datetime import timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database import Database, utcnow

router = Router()


def _as_utc(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.message(Command("stat"))
async def stat(message: Message, db: Database):
    data = await db.get_stats(message.from_user.id)
    user = data["user"]

    if not user:
        await message.answer("Start with /start first. 👋")
        return

    started = _as_utc(user.get("created_at", utcnow()))
    days = max(1, (utcnow() - started).days + 1)

    avg = f"{data['avg_score']:.1f}" if data["avg_score"] is not None else "—"
    best = f"{data['best_score']:.1f}" if data["best_score"] is not None else "—"

    topics = data["topics"]
    topic_text = ", ".join(topics[-10:]) if topics else "No topics yet"

    await message.answer(
        f"📊 <b>Your IELTS practice stats</b>\n\n"
        f"🔥 Days with the bot: <b>{days}</b>\n"
        f"🎤 Answers: <b>{data['attempts']}</b>\n"
        f"🧠 Topics practiced: <b>{len(topics)}</b>\n"
        f"📈 Average score: <b>{avg}</b>\n"
        f"🏆 Best score: <b>{best}</b>\n"
        f"📝 Last topic: <b>{data['last_topic'] or '—'}</b>\n\n"
        f"<b>Topics you've practiced</b>\n{topic_text}"
    )