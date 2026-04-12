from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import config

proxy_url = None
if all([config.proxy_protocol, config.proxy_login,
        config.proxy_password, config.proxy_ip,
        config.proxy_port]):
    proxy_url = f"{config.proxy_protocol}://{config.proxy_login}:{config.proxy_password}@{config.proxy_ip}:{config.proxy_port}"

bot = Bot(token=config.telegram_bot_token, proxy=proxy_url)
dp = Dispatcher(bot, storage=MemoryStorage())
