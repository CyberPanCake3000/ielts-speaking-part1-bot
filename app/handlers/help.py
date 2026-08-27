from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "<b>IELTS Speaking Practice</b> 🎤\n\n"
        "/topic — get a fresh Part 1 question\n"
        "/stat — see your progress\n"
        "/start — open the main menu and reminder settings\n"
        "/help — show this help\n\n"
        "For practice, answer with a voice message. "
        "I'll transcribe it and give you a short IELTS-style review."
    )
