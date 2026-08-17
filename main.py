import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.handlers.start import router as start_router
from bot.handlers.tasks import router as tasks_router
from bot.handlers.edit import router as edit_router
from bot.handlers.delete import router as delete_router
from bot.handlers.commands import router as commands_router


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_routers(
        start_router,
        tasks_router,
        commands_router,
        edit_router,
        delete_router,
    )

    logging.info("Бот запущен")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logging.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
