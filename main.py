import os
import asyncio
import logging

from aiogram import Bot
from aiogram.types import BotCommand
from sqlalchemy.orm import sessionmaker

from common.repository import bot, dp, config
from core.middlewares.db import DbMiddleware
from services.db.db_pool import create_db_pool
from core.filters.admin import AdminFilter

# NOT REMOVE THIS IMPORT!
from core.handlers import admin, student


logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Регистрация на мероприятие"),
    ]
    await bot.set_my_commands(commands)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        encoding="UTF-8",
        handlers=[
            #logging.FileHandler(os.path.join(config.logs_dir, "bot.log")),
            logging.StreamHandler()
        ]
    )
    logger.info("Starting bot")

    db_pool: sessionmaker = await create_db_pool(config.db_uri)

    await set_commands(bot)
    bot_obj = await bot.get_me()
    logger.info(f"Bot username: {bot_obj.username}")
    dp.middleware.setup(DbMiddleware(db_pool))
    dp.filters_factory.bind(AdminFilter)

    try:
        await dp.start_polling(allowed_updates=["message"])
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
