from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.database import Database, has_unlimited_access
from app.keyboards import main_menu, reminder_times, reminder_toggle

router = Router()


@router.message(CommandStart())
async def start(message: Message, db: Database):
    user = await db.get_user(message.from_user.id)

    await db.upsert_user(
        message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    if not user or not user.get("reminder_time"):
        await message.answer(
            "Hey! 👋\n\n"
            "I'm your IELTS Speaking practice partner.\n\n"
            "Use /topic to get a fresh IELTS Speaking Part 1 question, "
            "send me a voice answer, and I'll give you a friendly IELTS-style "
            "score and feedback.\n\n"
            "Before we start, choose a convenient daily reminder time:",
            reply_markup=reminder_times(),
        )
        return

    await message.answer(
        "Welcome back! 👋\n\n"
        "Ready for a quick IELTS Speaking practice?",
        reply_markup=main_menu(unlimited=has_unlimited_access(user)),
    )


@router.callback_query(F.data.startswith("set_time:"))
async def set_time(callback: CallbackQuery, db: Database):
    time = callback.data.split(":", 1)[1]
    await db.upsert_user(
        callback.from_user.id,
        reminder_enabled=True,
        reminder_time=time,
    )
    user = await db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"Perfect! I'll remind you every day at {time}. ⏰\n\n"
        "You can change this any time with /start.",
        reply_markup=main_menu(unlimited=has_unlimited_access(user)),
    )
    await callback.answer()


@router.callback_query(F.data == "reminder_settings")
async def settings(callback: CallbackQuery, db: Database):
    user = await db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"Daily reminders: {'ON' if user and user.get('reminder_enabled', True) else 'OFF'}\n"
        f"Time: {user.get('reminder_time', 'not set') if user else 'not set'}",
        reply_markup=reminder_toggle(bool(user and user.get("reminder_enabled", True))),
    )
    await callback.answer()


@router.callback_query(F.data == "reminder_toggle")
async def toggle(callback: CallbackQuery, db: Database):
    user = await db.get_user(callback.from_user.id)
    enabled = not bool(user and user.get("reminder_enabled", True))
    await db.upsert_user(callback.from_user.id, reminder_enabled=enabled)
    await callback.message.edit_text(
        f"Daily reminders are now {'ON 🔔' if enabled else 'OFF 🔕'}.",
        reply_markup=reminder_toggle(enabled),
    )
    await callback.answer()


@router.callback_query(F.data == "change_time")
async def change_time(callback: CallbackQuery):
    await callback.message.edit_text(
        "Choose your preferred daily reminder time:",
        reply_markup=reminder_times(),
    )
    await callback.answer()
