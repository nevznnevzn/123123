"""
Универсальный менеджер сессий для упрощения работы с базой данных.
Реализует принцип DRY для операций с БД.
"""

import functools
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from database_async import async_db_manager


def with_db_session(func: Callable) -> Callable:
    """
    Декоратор для автоматического управления сессией БД.
    Избавляет от необходимости каждый раз писать контекстный менеджер.

    Использование:
    @with_db_session
    async def my_function(session: AsyncSession, param1, param2):
        # Работа с БД через session
        pass

    # Вызов: await my_function(param1, param2)
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with async_db_manager.get_session() as session:
            return await func(session, *args, **kwargs)

    return wrapper


class DatabaseTransaction:
    """
    Контекстный менеджер для управления транзакциями БД.
    Позволяет выполнять несколько операций в одной транзакции.
    """

    def __init__(self):
        self.session = None

    async def __aenter__(self) -> AsyncSession:
        self.session = async_db_manager.async_session()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                await self.session.commit()
            else:
                await self.session.rollback()
        finally:
            await self.session.close()


@asynccontextmanager
async def db_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    Простой контекстный менеджер для транзакций.

    Использование:
    async with db_transaction() as session:
        # Несколько операций в одной транзакции
        user = User(name="test")
        session.add(user)
        # Автоматический commit при выходе
    """
    async with DatabaseTransaction() as session:
        yield session


def handle_db_errors(func: Callable) -> Callable:
    """
    Декоратор для обработки ошибок БД.
    Логирует ошибки и возвращает None при неудаче.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # В реальном проекте здесь должно быть логирование
            print(f"Database error in {func.__name__}: {e}")
            return None

    return wrapper


class QueryBuilder:
    """
    Упрощенный билдер запросов для частых операций.
    """

    def __init__(self, model_class):
        self.model_class = model_class
        self.session = None

    def with_session(self, session: AsyncSession):
        """Привязать сессию к билдеру"""
        self.session = session
        return self

    async def get_by_id(self, id_value: int):
        """Получить объект по ID"""
        return await self.session.get(self.model_class, id_value)

    async def get_by_field(self, field_name: str, field_value: Any):
        """Получить объект по значению поля"""
        from sqlalchemy import select

        field = getattr(self.model_class, field_name)
        stmt = select(self.model_class).where(field == field_value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_all(self) -> int:
        """Подсчитать все записи"""
        from sqlalchemy import func, select

        stmt = select(func.count(self.model_class.id))
        result = await self.session.execute(stmt)
        return result.scalar()


# Примеры использования новых утилит


@with_db_session
async def create_user_simple(session: AsyncSession, telegram_id: int, name: str):
    """Пример использования декоратора для создания пользователя"""
    from database_async import User

    user = User(telegram_id=telegram_id, name=name)
    session.add(user)
    await session.flush()  # Получить ID до commit
    return user


@handle_db_errors
@with_db_session
async def get_user_safe(session: AsyncSession, telegram_id: int):
    """Пример безопасного получения пользователя с обработкой ошибок"""
    from sqlalchemy import select

    from database_async import User

    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def bulk_operations_example():
    """Пример выполнения нескольких операций в одной транзакции"""
    from database_async import NatalChart, User

    async with db_transaction() as session:
        # Создаем пользователя
        user = User(telegram_id=12345, name="Test User")
        session.add(user)
        await session.flush()  # Получаем ID пользователя

        # Создаем карту для этого пользователя
        chart = NatalChart(
            user_id=user.id,
            city="Moscow",
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow",
            birth_date=datetime(1990, 1, 1),
            planets_data="{}",
        )
        session.add(chart)

        # Обе операции будут выполнены в одной транзакции
