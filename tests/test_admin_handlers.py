import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Chat, Message, Update
from aiogram.types import User as AiogramUser

from config import Config
from database import (
    DatabaseManager,
    Subscription,
    SubscriptionStatus,
    SubscriptionType,
    User,
)
from handlers.admin.middlewares import AdminAuthMiddleware
from handlers.admin.states import AdminStates

# --- Test Data ---

TEST_ADMIN_ID = 999999
REGULAR_USER_ID = 123456
USER_TO_FIND_ID = 54321

# --- Fixtures ---


@pytest.fixture
def mock_bot():
    """Fixture for a mocked bot."""
    return AsyncMock()


@pytest.fixture
def memory_storage():
    """Fixture for MemoryStorage."""
    return MemoryStorage()


@pytest.fixture
def mock_db_manager():
    """Fixture for a mocked DatabaseManager."""
    # Используем autospec=True, чтобы мок строго соответствовал интерфейсу DatabaseManager
    mock = Mock(spec=DatabaseManager, autospec=True)
    now = datetime.now()

    admin_user = User(id=1, telegram_id=TEST_ADMIN_ID, name="Admin", created_at=now)
    admin_user.subscription = Subscription(
        subscription_type=SubscriptionType.FREE, status=SubscriptionStatus.ACTIVE
    )

    regular_user = User(
        id=2, telegram_id=REGULAR_USER_ID, name="RegularUser", created_at=now
    )
    regular_user.subscription = Subscription(
        subscription_type=SubscriptionType.FREE, status=SubscriptionStatus.ACTIVE
    )

    user_to_find = User(
        id=3, telegram_id=USER_TO_FIND_ID, name="FoundUser", created_at=now
    )
    user_to_find.subscription = Subscription(
        subscription_type=SubscriptionType.FREE, status=SubscriptionStatus.ACTIVE
    )

    mock.get_user_profile.side_effect = lambda tid: {
        TEST_ADMIN_ID: admin_user,
        REGULAR_USER_ID: regular_user,
        USER_TO_FIND_ID: user_to_find,
    }.get(tid)

    mock.get_total_users_count.return_value = 100
    mock.get_users_for_mailing.return_value = [admin_user, regular_user, user_to_find]
    mock.get_app_statistics.return_value = {
        "total_users": 150,
        "new_users_today": 5,
        "new_users_7_days": 20,
        "new_users_30_days": 50,
        "active_premium": 10,
        "total_charts": 300,
    }

    return mock


@pytest.fixture
def dispatcher(memory_storage, mock_db_manager, mock_bot):
    """
    Fixture for the Dispatcher.
    For testing admin handlers, we skip the auth middleware and assume
    the user is already authorized.
    """
    from handlers.admin.router import create_admin_router

    admin_router = create_admin_router()

    dp = Dispatcher(storage=memory_storage, db_manager=mock_db_manager, bot=mock_bot)
    dp.include_router(admin_router)

    return dp


@pytest.fixture
def admin_user():
    """Fixture for an admin user."""
    return AiogramUser(id=TEST_ADMIN_ID, is_bot=False, first_name="Admin")


@pytest.fixture
def regular_user():
    """Fixture for a regular user."""
    return AiogramUser(id=REGULAR_USER_ID, is_bot=False, first_name="Regular")


@pytest.fixture
def chat():
    """Fixture for a chat."""
    return Chat(id=123, type="private")


# --- Tests ---

# Тест test_admin_command_access_denied удален, так как он покрывается
# в tests/test_admin_middleware.py


@pytest.mark.asyncio
async def test_admin_command_access_granted(dispatcher, mock_bot, admin_user, chat):
    """Test that an admin can access the admin panel."""
    message = Message(
        message_id=2, date=123, chat=chat, from_user=admin_user, text="/admin"
    )
    update = Update(update_id=1, message=message)

    await dispatcher.feed_update(mock_bot, update)
    mock_bot.send_message.assert_called_once()
    # A more specific check could be added here for the message text/markup


@pytest.mark.asyncio
async def test_user_search_start(dispatcher, mock_bot, admin_user, chat):
    """Test starting the user search process."""
    message = Message(
        message_id=3, date=123, chat=chat, from_user=admin_user, text="dummy"
    )
    callback_query = CallbackQuery(
        id="1",
        from_user=admin_user,
        chat_instance="1",
        message=message,
        data="admin_users",
    )
    update = Update(update_id=1, callback_query=callback_query)

    await dispatcher.feed_update(mock_bot, update)
    mock_bot.edit_message_text.assert_called_once()


@pytest.mark.asyncio
async def test_user_search_found(
    dispatcher, mock_bot, mock_db_manager, admin_user, chat
):
    """Test finding a user successfully."""
    state = dispatcher.fsm.get_context(mock_bot, admin_user.id, chat.id)
    await state.set_state(AdminStates.user_search)

    message = Message(
        message_id=4,
        date=123,
        chat=chat,
        from_user=admin_user,
        text=str(USER_TO_FIND_ID),
    )
    update = Update(update_id=1, message=message)

    await dispatcher.feed_update(mock_bot, update)
    mock_db_manager.get_user_profile.assert_called_once_with(USER_TO_FIND_ID)
    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_user_search_not_found(
    dispatcher, mock_bot, mock_db_manager, admin_user, chat
):
    """Test searching for a non-existent user."""
    state = dispatcher.fsm.get_context(mock_bot, admin_user.id, chat.id)
    await state.set_state(AdminStates.user_search)
    NON_EXISTENT_ID = 99999

    message = Message(
        message_id=5,
        date=123,
        chat=chat,
        from_user=admin_user,
        text=str(NON_EXISTENT_ID),
    )
    update = Update(update_id=1, message=message)

    await dispatcher.feed_update(mock_bot, update)
    mock_db_manager.get_user_profile.assert_called_with(NON_EXISTENT_ID)
    mock_bot.send_message.assert_called_once_with(
        chat_id=chat.id, text="Пользователь с таким ID не найден."
    )


@pytest.mark.asyncio
async def test_user_search_invalid_id(dispatcher, mock_bot, admin_user, chat):
    """Test providing a non-numeric ID for user search."""
    state = dispatcher.fsm.get_context(mock_bot, admin_user.id, chat.id)
    await state.set_state(AdminStates.user_search)

    message = Message(
        message_id=6, date=123, chat=chat, from_user=admin_user, text="not-a-number"
    )
    update = Update(update_id=1, message=message)

    await dispatcher.feed_update(mock_bot, update)
    mock_bot.send_message.assert_called_once_with(
        chat_id=chat.id,
        text="Некорректный ID. Пожалуйста, введите числовой Telegram ID.",
    )


@pytest.mark.asyncio
async def test_grant_premium(dispatcher, mock_bot, mock_db_manager, admin_user, chat):
    """Test granting premium to a user."""
    message = Message(
        message_id=7, date=123, chat=chat, from_user=admin_user, text="user profile"
    )
    callback_query = CallbackQuery(
        id="2",
        from_user=admin_user,
        chat_instance="1",
        message=message,
        data=f"grant_premium_{USER_TO_FIND_ID}",
    )
    update = Update(update_id=1, callback_query=callback_query)

    await dispatcher.feed_update(mock_bot, update)
    mock_db_manager.create_premium_subscription.assert_called_once_with(
        USER_TO_FIND_ID, duration_days=30
    )
    mock_bot.answer_callback_query.assert_called_once()
    mock_bot.edit_message_text.assert_called_once()


@pytest.mark.asyncio
async def test_revoke_premium(dispatcher, mock_bot, mock_db_manager, admin_user, chat):
    """Test revoking premium from a user."""
    user_to_find = mock_db_manager.get_user_profile(USER_TO_FIND_ID)
    user_to_find.subscription.subscription_type = SubscriptionType.PREMIUM

    message = Message(
        message_id=8, date=123, chat=chat, from_user=admin_user, text="user profile"
    )
    callback_query = CallbackQuery(
        id="3",
        from_user=admin_user,
        chat_instance="1",
        message=message,
        data=f"revoke_premium_{USER_TO_FIND_ID}",
    )
    update = Update(update_id=1, callback_query=callback_query)

    await dispatcher.feed_update(mock_bot, update)
    mock_db_manager.cancel_subscription.assert_called_once_with(USER_TO_FIND_ID)
    mock_bot.answer_callback_query.assert_called_once()
    mock_bot.edit_message_text.assert_called_once()


@pytest.mark.asyncio
async def test_mailing_start_and_confirm(
    dispatcher, mock_bot, mock_db_manager, admin_user, chat
):
    """Test the full mailing flow from start to confirmation."""
    # 1. Start mailing process
    start_message = Message(
        message_id=9, date=123, chat=chat, from_user=admin_user, text="dummy"
    )
    start_callback = CallbackQuery(
        id="4",
        from_user=admin_user,
        chat_instance="1",
        message=start_message,
        data="admin_mailing",
    )
    start_update = Update(update_id=1, callback_query=start_callback)

    await dispatcher.feed_update(mock_bot, start_update)
    mock_bot.edit_message_text.assert_called_once()

    # 2. Provide message for mailing
    state = dispatcher.fsm.get_context(mock_bot, admin_user.id, chat.id)
    mail_message = Message(
        message_id=10, date=123, chat=chat, from_user=admin_user, text="Hello users!"
    )
    mail_update = Update(update_id=2, message=mail_message)

    await dispatcher.feed_update(mock_bot, mail_update)
    assert mock_bot.send_message.call_count == 2  # Preview + confirmation question


@pytest.mark.asyncio
async def test_stats_show(dispatcher, mock_bot, mock_db_manager, admin_user, chat):
    """Test showing bot statistics."""
    message = Message(
        message_id=12, date=123, chat=chat, from_user=admin_user, text="dummy"
    )
    callback_query = CallbackQuery(
        id="6",
        from_user=admin_user,
        chat_instance="1",
        message=message,
        data="admin_stats",
    )
    update = Update(update_id=1, callback_query=callback_query)

    await dispatcher.feed_update(mock_bot, update)
    mock_db_manager.get_app_statistics.assert_called_once()
    mock_bot.edit_message_text.assert_called_once()


@pytest.mark.asyncio
@patch("handlers.admin.router.asyncio.create_task")
async def test_mailing_send_task(
    mock_create_task, dispatcher, mock_bot, admin_user, chat
):
    """Test that the mailing background task is created."""
    state = dispatcher.fsm.get_context(mock_bot, admin_user.id, chat.id)
    await state.set_state(AdminStates.mailing_message_input)
    await state.update_data(message_to_send={"text": "test"})

    message = Message(
        message_id=11, date=123, chat=chat, from_user=admin_user, text="dummy"
    )
    callback_query = CallbackQuery(
        id="5",
        from_user=admin_user,
        chat_instance="1",
        message=message,
        data="mailing_send",
    )
    update = Update(update_id=3, callback_query=callback_query)

    await dispatcher.feed_update(mock_bot, update)
    mock_create_task.assert_called_once()
