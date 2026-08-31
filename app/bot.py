from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.database import Database
from app.handlers import help, payments, practice, start, stats


def create_bot() -> Bot:
    from app.config import settings
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(db: Database) -> Dispatcher:
    dp = Dispatcher()
    dp["db"] = db

    dp.include_router(start.router)
    dp.include_router(practice.router)
    dp.include_router(stats.router)
    dp.include_router(payments.router)
    dp.include_router(help.router)

    return dp
