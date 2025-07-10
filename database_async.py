"""
Асинхронная версия DatabaseManager для улучшения производительности бота.
Использует aiosqlite и SQLAlchemy async для неблокирующих операций.
"""

import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    delete,
    func,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, selectinload

Base = declarative_base()


class SubscriptionType(Enum):
    """Типы подписки"""

    FREE = "free"
    PREMIUM = "premium"


class SubscriptionStatus(Enum):
    """Статусы подписки"""

    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# Используем те же модели, что и в синхронной версии
class User(Base):
    """Модель пользователя"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Поля профиля
    gender = Column(String(10), nullable=True)
    birth_year = Column(Integer, nullable=True)
    birth_city = Column(String(255), nullable=True)
    birth_date = Column(DateTime, nullable=True)
    birth_time_specified = Column(Boolean, default=True)

    is_profile_complete = Column(Boolean, default=False)
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    natal_charts = relationship(
        "NatalChart", back_populates="user", cascade="all, delete-orphan"
    )
    predictions = relationship(
        "Prediction", back_populates="user", cascade="all, delete-orphan"
    )
    subscription = relationship(
        "Subscription",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def is_premium(self) -> bool:
        """Проверяет, есть ли у пользователя активная премиум подписка"""
        if not self.subscription:
            return False
        return (
            self.subscription.is_active
            and self.subscription.subscription_type == SubscriptionType.PREMIUM
        )


class Subscription(Base):
    """Модель подписки пользователя"""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    subscription_type = Column(
        SQLEnum(SubscriptionType), nullable=False, default=SubscriptionType.FREE
    )
    status = Column(
        SQLEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE
    )

    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)

    payment_id = Column(String(255), nullable=True)
    payment_amount = Column(Float, nullable=True)
    payment_currency = Column(String(3), nullable=True, default="RUB")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscription")

    @property
    def is_active(self) -> bool:
        """Проверяет, активна ли подписка"""
        if self.status != SubscriptionStatus.ACTIVE:
            return False

        if self.end_date and datetime.utcnow() > self.end_date:
            return False

        return True

    @property
    def days_remaining(self) -> Optional[int]:
        """Возвращает количество оставшихся дней подписки"""
        if not self.end_date or not self.is_active:
            return None

        remaining = self.end_date - datetime.utcnow()
        return max(0, remaining.days)


class NatalChart(Base):
    """Модель натальной карты"""

    __tablename__ = "natal_charts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    chart_type = Column(String(10), default="own", nullable=False)
    chart_owner_name = Column(String(255), nullable=True)

    city = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone = Column(String(50), nullable=False)

    birth_date = Column(DateTime, nullable=False)
    birth_time_specified = Column(Boolean, default=True)
    has_warning = Column(Boolean, default=False)

    planets_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="natal_charts")
    predictions = relationship(
        "Prediction", back_populates="natal_chart", cascade="all, delete-orphan"
    )

    def get_planets_data(self) -> Dict[str, Any]:
        """Получить данные планет как словарь"""
        from models import PlanetPosition

        raw_data = json.loads(self.planets_data)
        planets_objects = {}
        for planet_name, position_data in raw_data.items():
            planets_objects[planet_name] = PlanetPosition(
                sign=position_data["sign"], degree=position_data["degree"]
            )
        return planets_objects

    def set_planets_data(self, data: Dict[str, Any]):
        """Сохранить данные планет как JSON"""
        self.planets_data = json.dumps(data, ensure_ascii=False, default=str)


class Prediction(Base):
    """Модель прогноза"""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    natal_chart_id = Column(Integer, ForeignKey("natal_charts.id"), nullable=False)

    prediction_type = Column(String(20), nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    generation_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="predictions")
    natal_chart = relationship("NatalChart", back_populates="predictions")

    def is_valid(self) -> bool:
        """Проверить, действителен ли прогноз"""
        now = datetime.utcnow()
        return self.valid_from <= now <= self.valid_until


class CompatibilityReport(Base):
    """Модель отчета по совместимости"""

    __tablename__ = "compatibility_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user_name = Column(String(255), nullable=False)
    partner_name = Column(String(255), nullable=False)

    user_birth_date = Column(DateTime, nullable=False)
    partner_birth_date = Column(DateTime, nullable=False)

    sphere = Column(String(50), nullable=False)
    report_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class AsyncDatabaseManager:
    """
    Асинхронный менеджер базы данных.
    Использует контекстные менеджеры для безопасной работы с сессиями.
    """

    def __init__(self, database_url: str = "sqlite+aiosqlite:///astro_bot.db"):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Создание таблиц базы данных"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Контекстный менеджер для работы с сессией БД.
        Автоматически закрывает сессию и откатывает транзакции при ошибках.
        """
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    # Методы для работы с пользователями
    async def get_or_create_user(
        self, telegram_id: int, name: str
    ) -> tuple[User, bool]:
        """Получить или создать пользователя"""
        async with self.get_session() as session:
            # Ищем существующего пользователя
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                # Обновляем имя если оно изменилось
                if user.name != name:
                    user.name = name
                    await session.commit()
                return user, False

            # Создаем нового пользователя
            user = User(telegram_id=telegram_id, name=name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user, True

    async def update_user_profile(
        self,
        telegram_id: int,
        name: str = None,
        gender: str = None,
        birth_year: int = None,
        birth_city: str = None,
        birth_date: datetime = None,
        birth_time_specified: bool = None,
    ) -> Optional[User]:
        """Обновить профиль пользователя"""
        async with self.get_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Обновляем поля
            if name is not None:
                user.name = name
            if gender is not None:
                user.gender = gender
            if birth_year is not None:
                user.birth_year = birth_year
            if birth_city is not None:
                user.birth_city = birth_city
            if birth_date is not None:
                user.birth_date = birth_date
            if birth_time_specified is not None:
                user.birth_time_specified = birth_time_specified

            # Проверяем завершенность профиля
            user.is_profile_complete = all(
                [
                    user.name,
                    user.gender,
                    user.birth_year,
                    user.birth_city,
                    user.birth_date,
                ]
            )

            await session.commit()
            await session.refresh(user)
            return user

    async def get_user_profile(self, telegram_id: int) -> Optional[User]:
        """Получить профиль пользователя"""
        async with self.get_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def set_notifications(self, telegram_id: int, enabled: bool) -> bool:
        """Установить настройки уведомлений"""
        async with self.get_session() as session:
            stmt = (
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(notifications_enabled=enabled)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    # Методы для работы с натальными картами
    async def create_natal_chart(
        self,
        telegram_id: int,
        name: str,
        city: str,
        latitude: float,
        longitude: float,
        timezone: str,
        birth_date: datetime,
        birth_time_specified: bool,
        has_warning: bool,
        planets_data: Dict[str, Any],
        chart_type: str = "own",
        chart_owner_name: str = None,
    ) -> NatalChart:
        """Создать натальную карту"""
        async with self.get_session() as session:
            # Получаем пользователя
            user, _ = await self.get_or_create_user(telegram_id, name)

            chart = NatalChart(
                user_id=user.id,
                chart_type=chart_type,
                chart_owner_name=chart_owner_name,
                city=city,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
                birth_date=birth_date,
                birth_time_specified=birth_time_specified,
                has_warning=has_warning,
            )
            chart.set_planets_data(planets_data)

            session.add(chart)
            await session.commit()
            await session.refresh(chart)
            return chart

    async def get_user_charts(self, telegram_id: int) -> List[NatalChart]:
        """Получить все карты пользователя"""
        async with self.get_session() as session:
            stmt = (
                select(NatalChart)
                .join(User)
                .where(User.telegram_id == telegram_id)
                .order_by(NatalChart.created_at.desc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def find_existing_chart(
        self, telegram_id: int, city: str, birth_date: datetime
    ) -> Optional[NatalChart]:
        """Найти существующую карту"""
        async with self.get_session() as session:
            stmt = (
                select(NatalChart)
                .join(User)
                .where(
                    User.telegram_id == telegram_id,
                    NatalChart.city == city,
                    NatalChart.birth_date == birth_date,
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    # Методы для работы с прогнозами
    async def find_valid_prediction(
        self, telegram_id: int, chart_id: int, prediction_type: str
    ) -> Optional[Prediction]:
        """Найти действующий прогноз"""
        async with self.get_session() as session:
            now = datetime.utcnow()
            stmt = (
                select(Prediction)
                .join(User)
                .where(
                    User.telegram_id == telegram_id,
                    Prediction.natal_chart_id == chart_id,
                    Prediction.prediction_type == prediction_type,
                    Prediction.valid_from <= now,
                    Prediction.valid_until >= now,
                )
                .order_by(Prediction.created_at.desc())
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create_prediction(
        self,
        telegram_id: int,
        chart_id: int,
        prediction_type: str,
        valid_from: datetime,
        valid_until: datetime,
        content: str,
        generation_time: float = None,
    ) -> Prediction:
        """Создать прогноз"""
        async with self.get_session() as session:
            user, _ = await self.get_or_create_user(telegram_id, "Unknown")

            prediction = Prediction(
                user_id=user.id,
                natal_chart_id=chart_id,
                prediction_type=prediction_type,
                valid_from=valid_from,
                valid_until=valid_until,
                content=content,
                generation_time=generation_time,
            )

            session.add(prediction)
            await session.commit()
            await session.refresh(prediction)
            return prediction

    # Методы для работы с подписками
    async def get_or_create_subscription(self, telegram_id: int) -> Subscription:
        """Получить или создать подписку"""
        async with self.get_session() as session:
            user, _ = await self.get_or_create_user(telegram_id, "Unknown")

            stmt = select(Subscription).where(Subscription.user_id == user.id)
            result = await session.execute(stmt)
            subscription = result.scalar_one_or_none()

            if not subscription:
                subscription = Subscription(
                    user_id=user.id,
                    subscription_type=SubscriptionType.FREE,
                    status=SubscriptionStatus.ACTIVE,
                )
                session.add(subscription)
                await session.commit()
                await session.refresh(subscription)

            return subscription

    # Статистические методы
    async def get_total_users_count(self) -> int:
        """Получить общее количество пользователей"""
        async with self.get_session() as session:
            stmt = select(func.count(User.id))
            result = await session.execute(stmt)
            return result.scalar()

    async def get_app_statistics(self) -> Dict[str, int]:
        """Получить статистику приложения"""
        async with self.get_session() as session:
            # Общее количество пользователей
            total_users_stmt = select(func.count(User.id))
            total_users = await session.scalar(total_users_stmt)

            # Новые пользователи за сегодня
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            new_users_today_stmt = select(func.count(User.id)).where(
                User.created_at >= today
            )
            new_users_today = await session.scalar(new_users_today_stmt)

            # Новые пользователи за неделю
            week_ago = today - timedelta(days=7)
            new_users_7_days_stmt = select(func.count(User.id)).where(
                User.created_at >= week_ago
            )
            new_users_7_days = await session.scalar(new_users_7_days_stmt)

            # Новые пользователи за месяц
            month_ago = today - timedelta(days=30)
            new_users_30_days_stmt = select(func.count(User.id)).where(
                User.created_at >= month_ago
            )
            new_users_30_days = await session.scalar(new_users_30_days_stmt)

            # Активные премиум подписки
            active_premium_stmt = select(func.count(Subscription.id)).where(
                Subscription.subscription_type == SubscriptionType.PREMIUM,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
            active_premium = await session.scalar(active_premium_stmt)

            # Общее количество карт
            total_charts_stmt = select(func.count(NatalChart.id))
            total_charts = await session.scalar(total_charts_stmt)

            return {
                "total_users": total_users or 0,
                "new_users_today": new_users_today or 0,
                "new_users_7_days": new_users_7_days or 0,
                "new_users_30_days": new_users_30_days or 0,
                "active_premium": active_premium or 0,
                "total_charts": total_charts or 0,
            }

    async def cleanup_expired_predictions(self) -> int:
        """Очистить устаревшие прогнозы"""
        async with self.get_session() as session:
            now = datetime.utcnow()
            stmt = delete(Prediction).where(Prediction.valid_until < now)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    async def close(self):
        """Закрыть соединение с базой данных"""
        await self.engine.dispose()


# Глобальный экземпляр асинхронного менеджера
async_db_manager = AsyncDatabaseManager()
