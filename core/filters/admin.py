from aiogram.dispatcher.filters import BoundFilter
from aiogram.types.base import TelegramObject

from config import config


class AdminFilter(BoundFilter):
    async def check(self, obj: TelegramObject) -> bool:
        user = getattr(obj, "from_user", None)
        if user is None:
            return False
        return user.id in config.admin_ids

