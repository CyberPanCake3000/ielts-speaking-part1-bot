import asyncio
import logging

from aiohttp import web

from app.bot import create_bot, create_dispatcher
from app.config import settings
from app.database import Database
from app.scheduler import ReminderScheduler


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def health_server() -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.app_host, settings.app_port)
    await site.start()
    return runner


async def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    db = Database(settings.mongodb_uri, settings.mongodb_db)
    await db.connect()

    bot = create_bot()
    dp = create_dispatcher(db)

    reminders = ReminderScheduler(bot, db)
    await reminders.start()

    health_runner = await health_server()

    try:
        await dp.start_polling(bot)
    finally:
        await reminders.stop()
        await health_runner.cleanup()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
