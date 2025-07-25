from unittest.mock import AsyncMock

import pytest

from database import DatabaseManager
from handlers.profile.router import create_profile_router
from keyboards import Keyboards
from services.astro_calculations import AstroService


@pytest.fixture
def db_manager():
    """Создает экземпляр DatabaseManager с базой данных в памяти для каждого теста."""
    return DatabaseManager(database_url="sqlite:///:memory:")


@pytest.mark.asyncio
async def test_toggle_notifications_handler(db_manager):
    """
    Тест проверяет, что обработчик 'toggle_notifications_handler'
    корректно изменяет статус уведомлений в БД и обновляет клавиатуру.
    """
    # --- 1. Подготовка ---
    # Создаем зависимости и роутер
    astro_service = (
        AstroService()
    )  # Для этого теста он не важен, но нужен для создания роутера
    profile_router = create_profile_router(db_manager, astro_service, async_db_manager)

    # Находим наш обработчик в списке обработчиков роутера.
    # Это не самый элегантный способ, но он работает для тестирования.
    handler_object = None
    for h in profile_router.callback_query.handlers:
        if h.callback.__name__ == "toggle_notifications_handler":
            handler_object = h
            break

    assert (
        handler_object is not None
    ), "Обработчик toggle_notifications_handler не найден"

    # Создаем пользователя
    telegram_id = 54321
    user, _ = db_manager.get_or_create_user(telegram_id=telegram_id, name="Toggler")
    assert user.notifications_enabled is True

    # Создаем мок CallbackQuery
    mock_callback = AsyncMock()
    mock_callback.from_user.id = telegram_id
    mock_callback.message.edit_reply_markup = AsyncMock()

    # --- 2. Вызов обработчика (выключение) ---
    await handler_object.callback(mock_callback)

    # --- 3. Проверка результата ---
    updated_user = db_manager.get_user_profile(telegram_id)
    assert updated_user.notifications_enabled is False
    mock_callback.message.edit_reply_markup.assert_called_once_with(
        reply_markup=Keyboards.profile_menu(notifications_enabled=False)
    )
    mock_callback.answer.assert_called_once_with("Ежедневные уведомления выключены.")

    # --- 4. Повторный вызов (включение) ---
    mock_callback.reset_mock()
    mock_callback.message.edit_reply_markup.reset_mock()

    await handler_object.callback(mock_callback)

    # --- 5. Проверка результата ---
    updated_user_again = db_manager.get_user_profile(telegram_id)
    assert updated_user_again.notifications_enabled is True
    mock_callback.message.edit_reply_markup.assert_called_once_with(
        reply_markup=Keyboards.profile_menu(notifications_enabled=True)
    )
    mock_callback.answer.assert_called_once_with("Ежедневные уведомления включены.")
