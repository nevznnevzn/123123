from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import User

from handlers.admin.middlewares import AdminAuthMiddleware

ADMIN_ID = 12345
REGULAR_ID = 54321


@pytest.mark.asyncio
async def test_admin_auth_middleware_pass():
    """Тест: middleware пропускает администратора."""
    middleware = AdminAuthMiddleware(admin_ids=[ADMIN_ID])
    handler = AsyncMock()

    event = MagicMock()
    data = {"event_from_user": User(id=ADMIN_ID, is_bot=False, first_name="Admin")}

    await middleware(handler=handler, event=event, data=data)

    handler.assert_called_once_with(event, data)


@pytest.mark.asyncio
async def test_admin_auth_middleware_block():
    """Тест: middleware блокирует обычного пользователя."""
    middleware = AdminAuthMiddleware(admin_ids=[ADMIN_ID])
    handler = AsyncMock()

    event = MagicMock()
    data = {"event_from_user": User(id=REGULAR_ID, is_bot=False, first_name="User")}

    await middleware(handler=handler, event=event, data=data)

    handler.assert_not_called()
