"""
Глобальная конфигурация pytest для тестирования астрологического бота.
Содержит общие фикстуры и настройки для асинхронных тестов.
"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database_async import AsyncDatabaseManager, Base, NatalChart, Subscription, User


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для всей сессии тестирования"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncDatabaseManager, None]:
    """
    Создает временную базу данных в памяти для тестов.
    Каждый тест получает чистую БД.
    """
    # Используем SQLite в памяти для тестов
    db_manager = AsyncDatabaseManager("sqlite+aiosqlite:///:memory:")

    # Создаем таблицы
    await db_manager.init_db()

    yield db_manager

    # Закрываем соединение
    await db_manager.close()


@pytest.fixture
async def test_session(
    test_db: AsyncDatabaseManager,
) -> AsyncGenerator[AsyncSession, None]:
    """Создает сессию БД для тестов"""
    async with test_db.get_session() as session:
        yield session


@pytest.fixture
async def sample_user(test_db: AsyncDatabaseManager) -> User:
    """Создает тестового пользователя"""
    user, _ = await test_db.get_or_create_user(telegram_id=123456789, name="Test User")
    return user


@pytest.fixture
async def sample_natal_chart(
    test_db: AsyncDatabaseManager, sample_user: User
) -> NatalChart:
    """Создает тестовую натальную карту"""
    planets_data = {
        "Солнце": {"sign": "Козерог", "degree": 15.5},
        "Луна": {"sign": "Рыбы", "degree": 23.2},
    }

    chart = await test_db.create_natal_chart(
        telegram_id=sample_user.telegram_id,
        name=sample_user.name,
        city="Moscow",
        latitude=55.7558,
        longitude=37.6176,
        timezone="Europe/Moscow",
        birth_date=datetime(1990, 1, 1, 12, 0),
        birth_time_specified=True,
        has_warning=False,
        planets_data=planets_data,
    )
    return chart


@pytest.fixture
def mock_bot():
    """Мок Telegram бота"""
    bot = Mock()
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.delete_message = AsyncMock()
    return bot


@pytest.fixture
def mock_message():
    """Мок Telegram сообщения"""
    message = Mock()
    message.from_user.id = 123456789
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.chat.id = 123456789
    message.text = "test message"
    message.message_id = 1
    return message


@pytest.fixture
def mock_callback_query():
    """Мок Telegram callback query"""
    callback = Mock()
    callback.from_user.id = 123456789
    callback.from_user.first_name = "Test"
    callback.from_user.last_name = "User"
    callback.message.chat.id = 123456789
    callback.data = "test_callback"
    callback.answer = AsyncMock()
    return callback


@pytest.fixture
def mock_astro_calculations():
    """Мок астрологических расчетов"""
    with pytest.mock.patch("services.astro_calculations.AstroCalculations") as mock:
        mock_instance = Mock()
        mock_instance.calculate_natal_chart.return_value = {
            "Солнце": {"sign": "Козерог", "degree": 15.5},
            "Луна": {"sign": "Рыбы", "degree": 23.2},
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_ai_service():
    """Мок ИИ сервиса для прогнозов"""
    with pytest.mock.patch("services.ai_predictions.AIPredictionService") as mock:
        mock_instance = Mock()
        mock_instance.get_chat_completion = AsyncMock(return_value="Тестовый прогноз")
        mock.return_value = mock_instance
        yield mock_instance


# Маркеры для категоризации тестов
pytest_plugins = ["pytest_asyncio"]


# Настройки для различных типов тестов
def pytest_configure(config):
    """Конфигурация pytest"""
    config.addinivalue_line("markers", "unit: единичные тесты")
    config.addinivalue_line("markers", "integration: интеграционные тесты")
    config.addinivalue_line("markers", "slow: медленные тесты")
    config.addinivalue_line("markers", "database: тесты с БД")
    config.addinivalue_line("markers", "astro: астрологические расчеты")


def pytest_collection_modifyitems(config, items):
    """Автоматически помечает тесты маркерами"""
    for item in items:
        # Помечаем все async тесты
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

        # Помечаем тесты БД
        if "test_db" in item.fixturenames or "test_session" in item.fixturenames:
            item.add_marker(pytest.mark.database)

        # Помечаем астрологические тесты
        if "astro" in item.name.lower() or "natal" in item.name.lower():
            item.add_marker(pytest.mark.astro)


# Утилитарные функции для тестов
class TestDataFactory:
    """Фабрика тестовых данных"""

    @staticmethod
    def create_user_data(telegram_id: int = 123456789) -> dict:
        """Создает данные тестового пользователя"""
        return {
            "telegram_id": telegram_id,
            "name": "Test User",
            "gender": "Мужской",
            "birth_year": 1990,
            "birth_city": "Moscow",
            "birth_date": datetime(1990, 1, 1, 12, 0),
        }

    @staticmethod
    def create_natal_chart_data() -> dict:
        """Создает данные тестовой натальной карты"""
        return {
            "city": "Moscow",
            "latitude": 55.7558,
            "longitude": 37.6176,
            "timezone": "Europe/Moscow",
            "birth_date": datetime(1990, 1, 1, 12, 0),
            "birth_time_specified": True,
            "has_warning": False,
            "planets_data": {
                "Солнце": {"sign": "Козерог", "degree": 15.5},
                "Луна": {"sign": "Рыбы", "degree": 23.2},
                "Меркурий": {"sign": "Стрелец", "degree": 28.1},
                "Венера": {"sign": "Водолей", "degree": 5.7},
                "Марс": {"sign": "Стрелец", "degree": 12.3},
            },
        }


@pytest.fixture
def test_data_factory():
    """Предоставляет фабрику тестовых данных"""
    return TestDataFactory()
