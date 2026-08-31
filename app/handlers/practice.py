import tempfile
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.ai.claude import ClaudeService
from app.ai.stt import SpeechToTextService
from app.config import settings
from app.database import Database, has_unlimited_access, utcnow
from app.keyboards import main_menu, paywall_menu

router = Router()
claude = ClaudeService()
stt = SpeechToTextService()


def format_evaluation(e) -> str:
    corrections = "\n".join(
        f"• <b>{c['original']}</b> → <b>{c['correction']}</b>\n  {c['why']}"
        for c in e.corrections[:5]
    ) or "No major grammar issues spotted — nice!"

    good = "\n".join(f"• {x}" for x in e.good_points[:3])
    improvements = "\n".join(f"• {x}" for x in e.improvements[:3])

    return (
        f"🏆 <b>Estimated IELTS score: {e.overall_score:.1f}</b>\n\n"
        f"<b>Breakdown</b>\n"
        f"Fluency & Coherence: {e.fluency_coherence:.1f}\n"
        f"Lexical Resource: {e.lexical_resource:.1f}\n"
        f"Grammar: {e.grammatical_accuracy:.1f}\n"
        f"Pronunciation: {e.pronunciation:.1f}\n\n"
        f"<b>What you did well</b>\n{good}\n\n"
        f"<b>Quick corrections</b>\n{corrections}\n\n"
        f"<b>Next time</b>\n{improvements}\n\n"
        f"<b>Band 7-style example</b>\n{e.band_7_example}\n\n"
        f"💬 <b>Verdict</b>\n{e.verdict}"
    )


async def run_topic(message: Message, db: Database, telegram_id: int):
    user = await db.get_user(telegram_id)
    if not has_unlimited_access(user):
        used = await db.count_attempts(telegram_id)
        if used >= settings.free_attempts_limit:
            if not await db.consume_extra_attempt(telegram_id):
                await message.answer(
                    f"🔒 You've used all {settings.free_attempts_limit} free practice attempts.\n\n"
                    "Get more practice with Telegram Stars:",
                    reply_markup=paywall_menu(),
                )
                return

    recent = await db.db.attempts.find(
        {"telegram_id": telegram_id},
        {"topic": 1, "_id": 0},
        sort=[("created_at", -1)],
        limit=30,
    ).to_list(30)
    previous_topics = [x["topic"] for x in recent]

    topic = await claude.generate_part1_topic(previous_topics)

    await db.upsert_user(
        telegram_id,
        current_topic=topic.topic,
        current_question=topic.question,
        waiting_for_voice=True,
    )

    await message.answer(
        f"🎤 <b>IELTS Speaking Part 1</b>\n\n"
        f"<b>Topic:</b> {topic.topic}\n\n"
        f"<b>Question:</b> {topic.question}\n\n"
        "Send me your answer as a voice message. Try to speak naturally — "
        "don't worry about making mistakes!"
    )


@router.message(Command("topic"))
async def topic_command(message: Message, db: Database):
    await run_topic(message, db, message.from_user.id)


@router.callback_query(F.data == "practice")
async def topic_callback(callback: CallbackQuery, db: Database):
    await run_topic(callback.message, db, callback.from_user.id)
    await callback.answer()


@router.message(F.voice)
async def voice_answer(message: Message, db: Database):
    user = await db.get_user(message.from_user.id)

    if not user or not user.get("waiting_for_voice"):
        await message.answer("Use /topic first, then send your voice answer. 🎤")
        return

    voice = message.voice

    if voice.duration > settings.max_voice_duration_seconds:
        await message.answer(
            f"Your answer is a little long. Please keep it under "
            f"{settings.max_voice_duration_seconds} seconds for Part 1."
        )
        return

    await message.answer("Got it! 🎧 I'm listening and checking your answer...")

    bot = message.bot
    file = await bot.get_file(voice.file_id)

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = Path(tmp) / "answer.ogg"
        await bot.download_file(file.file_path, destination=audio_path)
        transcript = await stt.transcribe(audio_path)

    if not transcript:
        await message.answer("I couldn't understand the recording. Could you try again?")
        return

    evaluation = await claude.evaluate(
        user["current_topic"],
        user["current_question"],
        transcript,
    )

    await db.save_attempt({
        "telegram_id": message.from_user.id,
        "topic": user["current_topic"],
        "question": user["current_question"],
        "transcript": transcript,
        "overall_score": evaluation.overall_score,
        "fluency_coherence": evaluation.fluency_coherence,
        "lexical_resource": evaluation.lexical_resource,
        "grammatical_accuracy": evaluation.grammatical_accuracy,
        "pronunciation": evaluation.pronunciation,
        "evaluation": evaluation.model_dump(),
        "telegram_voice_file_id": voice.file_id,
        "created_at": utcnow(),
    })

    await db.upsert_user(
        message.from_user.id,
        waiting_for_voice=False,
        current_topic=None,
        current_question=None,
    )

    user = await db.get_user(message.from_user.id)
    await message.answer(
        f"<b>Your transcript</b>\n{transcript}\n\n"
        + format_evaluation(evaluation),
        reply_markup=main_menu(unlimited=has_unlimited_access(user)),
    )