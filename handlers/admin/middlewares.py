from typing import Any, Awaitable, Callable, Dict, List

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class AdminAuthMiddleware(BaseMiddleware):
    """
    Middleware для проверки, является ли пользователь администратором.
    """

    def __init__(self, admin_ids: List[int]):
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        user_id = data.get("event_from_user").id

        if user_id not in self.admin_ids:
            return

        return await handler(event, data)
