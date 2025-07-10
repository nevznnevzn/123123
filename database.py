import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

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
    create_engine,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, joinedload, relationship, sessionmaker

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


class User(Base):
    """Модель пользователя"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Поля профиля
    gender = Column(String(10), nullable=True)  # "Мужской" или "Женский"
    birth_year = Column(Integer, nullable=True)
    birth_city = Column(String(255), nullable=True)
    birth_date = Column(DateTime, nullable=True)  # Дата и время рождения
    birth_time_specified = Column(Boolean, default=True)  # Было ли указано время

    # Флаг завершенности профиля
    is_profile_complete = Column(Boolean, default=False)

    # Настройки уведомлений
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

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, name='{self.name}', profile_complete={self.is_profile_complete})>"

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

    # Даты подписки
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)  # Null для бессрочной подписки

    # Информация о платеже
    payment_id = Column(String(255), nullable=True)  # ID платежа в платежной системе
    payment_amount = Column(Float, nullable=True)  # Сумма платежа
    payment_currency = Column(String(3), nullable=True, default="RUB")  # Валюта

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, type={self.subscription_type}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Проверяет, активна ли подписка"""
        if self.status != SubscriptionStatus.ACTIVE:
            return False

        # Проверяем дату окончания (если она есть)
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

    # Тип карты: "own" или "other"
    chart_type = Column(String(10), default="own", nullable=False)
    chart_owner_name = Column(
        String(255), nullable=True
    )  # Имя владельца (для чужих карт)

    # Данные места рождения
    city = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone = Column(String(50), nullable=False)

    # Данные времени рождения
    birth_date = Column(DateTime, nullable=False)
    birth_time_specified = Column(Boolean, default=True)  # Было ли указано точное время
    has_warning = Column(
        Boolean, default=False
    )  # Есть ли предупреждение о неточном времени

    # Данные расчетов (JSON)
    planets_data = Column(Text, nullable=False)  # JSON с данными планет

    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь с пользователем
    user = relationship("User", back_populates="natal_charts")
    predictions = relationship(
        "Prediction", back_populates="natal_chart", cascade="all, delete-orphan"
    )

    def get_planets_data(self) -> Dict[str, "PlanetPosition"]:
        """Получить данные планет как словарь объектов PlanetPosition"""
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

    def __repr__(self):
        return f"<NatalChart(user_id={self.user_id}, type='{self.chart_type}', city='{self.city}', birth_date='{self.birth_date}')>"


class Prediction(Base):
    """Модель прогноза"""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    natal_chart_id = Column(Integer, ForeignKey("natal_charts.id"), nullable=False)

    # Тип прогноза: "сегодня", "неделя", "месяц", "квартал"
    prediction_type = Column(String(20), nullable=False)

    # Период действия прогноза
    valid_from = Column(DateTime, nullable=False)  # С какой даты действует
    valid_until = Column(DateTime, nullable=False)  # До какой даты действует

    # Содержимое прогноза
    content = Column(Text, nullable=False)  # Текст прогноза

    # Время генерации
    generation_time = Column(Float, nullable=True)  # Время генерации в секундах

    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="predictions")
    natal_chart = relationship("NatalChart", back_populates="predictions")

    def is_valid(self) -> bool:
        """Проверить, действителен ли прогноз"""
        now = datetime.utcnow()
        return self.valid_from <= now <= self.valid_until

    def __repr__(self):
        return f"<Prediction(user_id={self.user_id}, type='{self.prediction_type}', valid_until='{self.valid_until}')>"


class CompatibilityReport(Base):
    """Модель отчета по совместимости"""

    __tablename__ = "compatibility_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user_name = Column(String(255), nullable=False)
    partner_name = Column(String(255), nullable=False)

    # Сохраняем дату и город для обоих, чтобы можно было идентифицировать отчет
    user_birth_date = Column(DateTime, nullable=False)
    partner_birth_date = Column(DateTime, nullable=False)

    sphere = Column(String(50), nullable=False)  # 'love', 'career', 'friendship'
    report_text = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

    def __repr__(self):
        return f"<CompatibilityReport(user='{self.user_name}', partner='{self.partner_name}', sphere='{self.sphere}')>"


class DatabaseManager:
    """Менеджер для работы с базой данных"""

    def __init__(self, database_url: str = "sqlite:///astro_bot.db"):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Создаем таблицы
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Получить сессию базы данных"""
        return self.SessionLocal()

    def get_or_create_user(self, telegram_id: int, name: str) -> tuple[User, bool]:
        """Получить или создать пользователя

        Returns:
            tuple[User, bool]: (пользователь, был_ли_создан)
        """
        with self.get_session() as session:
            user = (
                session.query(User)
                .options(joinedload(User.subscription))
                .filter(User.telegram_id == telegram_id)
                .first()
            )

            if not user:
                user = User(telegram_id=telegram_id, name=name)
                session.add(user)
                session.commit()
                session.refresh(user)
                return user, True  # Пользователь был создан
            else:
                # Обновляем имя если изменилось
                if user.name != name:
                    user.name = name
                    session.commit()
                return user, False  # Пользователь уже существовал

    def update_user_profile(
        self,
        telegram_id: int,
        name: str = None,
        gender: str = None,
        birth_year: int = None,
        birth_city: str = None,
        birth_date: datetime = None,
        birth_time_specified: bool = None,
    ) -> Optional[User]:
        """Обновить или создать профиль пользователя."""
        with self.get_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()

            if not user:
                # Если пользователь не найден, создаем его
                if not name:
                    return None
                user = User(telegram_id=telegram_id, name=name)
                session.add(user)

            # Обновляем поля, если переданы значения
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

            # Проверяем, заполнен ли профиль полностью
            is_complete = all(
                [user.name, user.gender, user.birth_date, user.birth_city]
            )
            user.is_profile_complete = is_complete

            session.commit()
            session.refresh(user)
            return user

    def get_user_profile(self, telegram_id: int) -> Optional[User]:
        """Получить профиль пользователя"""
        with self.get_session() as session:
            return (
                session.query(User)
                .options(joinedload(User.subscription))
                .filter(User.telegram_id == telegram_id)
                .first()
            )

    def set_notifications(self, telegram_id: int, enabled: bool) -> bool:
        """Включить или выключить уведомления для пользователя."""
        with self.get_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.notifications_enabled = enabled
                session.commit()
                return True
            return False

    def get_total_users_count(self) -> int:
        """Возвращает общее количество пользователей в базе."""
        with self.get_session() as session:
            return session.query(func.count(User.id)).scalar()

    def get_users_for_mailing(self) -> List[User]:
        """Получить всех пользователей, у которых включены уведомления."""
        with self.get_session() as session:
            return session.query(User).filter(User.notifications_enabled == True).all()

    def find_existing_chart(
        self, telegram_id: int, city: str, birth_date: datetime
    ) -> Optional[NatalChart]:
        """Найти существующую натальную карту с такими же данными"""
        with self.get_session() as session:
            chart = (
                session.query(NatalChart)
                .join(User)
                .filter(
                    User.telegram_id == telegram_id,
                    NatalChart.city == city,
                    NatalChart.birth_date == birth_date,
                )
                .first()
            )

            return chart

    def create_natal_chart(
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
        """Создать новую натальную карту"""
        with self.get_session() as session:
            # Получаем пользователя в текущей сессии
            user = session.query(User).filter(User.telegram_id == telegram_id).first()

            if not user:
                # Если пользователя нет, создаем его
                user = User(telegram_id=telegram_id, name=name)
                session.add(user)
                session.flush()  # Получаем ID без commit

            # Создаем натальную карту
            new_chart = NatalChart(
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

            if planets_data:
                # Проверяем, являются ли данные датаклассами и конвертируем в dict
                first_value = next(iter(planets_data.values()), None)
                if first_value and is_dataclass(first_value):
                    planets_data_dict = {
                        name: asdict(pos) for name, pos in planets_data.items()
                    }
                    new_chart.set_planets_data(planets_data_dict)
                else:
                    # Если это уже dict или что-то другое, сохраняем как есть
                    new_chart.set_planets_data(planets_data)
            else:
                new_chart.set_planets_data({})

            session.add(new_chart)
            session.commit()
            session.refresh(new_chart)

            return new_chart

    def get_user_charts(self, telegram_id: int) -> List[NatalChart]:
        """Получить все натальные карты пользователя"""
        with self.get_session() as session:
            charts = (
                session.query(NatalChart)
                .join(User)
                .filter(User.telegram_id == telegram_id)
                .order_by(NatalChart.created_at.desc())
                .all()
            )

            return charts

    def get_chart_by_id(self, chart_id: int, telegram_id: int) -> Optional[NatalChart]:
        """Получить натальную карту по ID (с проверкой владельца)"""
        with self.get_session() as session:
            chart = (
                session.query(NatalChart)
                .join(User)
                .filter(NatalChart.id == chart_id, User.telegram_id == telegram_id)
                .first()
            )

            return chart

    def delete_natal_chart(self, chart_id: int, telegram_id: int) -> bool:
        """Удалить натальную карту (с проверкой владельца)"""
        with self.get_session() as session:
            chart = (
                session.query(NatalChart)
                .join(User)
                .filter(NatalChart.id == chart_id, User.telegram_id == telegram_id)
                .first()
            )

            if chart:
                session.delete(chart)
                session.commit()
                return True

            return False

    def delete_user_completely(self, telegram_id: int) -> tuple[bool, int]:
        """Полностью удалить пользователя и все его натальные карты (для отладки)

        Returns:
            tuple[bool, int]: (успех, количество_удаленных_карт)
        """
        with self.get_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()

            if not user:
                return False, 0

            # Подсчитываем количество карт перед удалением
            charts_count = len(user.natal_charts)

            # Удаляем пользователя (каскадно удалятся и все его карты благодаря cascade="all, delete-orphan")
            session.delete(user)
            session.commit()

            return True, charts_count

    def find_valid_prediction(
        self, telegram_id: int, chart_id: int, prediction_type: str
    ) -> Optional[Prediction]:
        """Найти действующий прогноз для карты и типа"""
        with self.get_session() as session:
            now = datetime.utcnow()

            prediction = (
                session.query(Prediction)
                .join(User)
                .filter(
                    User.telegram_id == telegram_id,
                    Prediction.natal_chart_id == chart_id,
                    Prediction.prediction_type == prediction_type,
                    Prediction.valid_from <= now,
                    Prediction.valid_until >= now,
                )
                .first()
            )

            return prediction

    def create_prediction(
        self,
        telegram_id: int,
        chart_id: int,
        prediction_type: str,
        valid_from: datetime,
        valid_until: datetime,
        content: str,
        generation_time: float = None,
    ) -> Prediction:
        """Создать новый прогноз"""
        with self.get_session() as session:
            # Получаем пользователя
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден")

            # Создаем прогноз
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
            session.commit()
            session.refresh(prediction)

            return prediction

    def get_user_predictions(
        self, telegram_id: int, active_only: bool = True
    ) -> List[Prediction]:
        """Получить прогнозы пользователя"""
        with self.get_session() as session:
            query = (
                session.query(Prediction)
                .join(User)
                .filter(User.telegram_id == telegram_id)
            )

            if active_only:
                now = datetime.utcnow()
                query = query.filter(
                    Prediction.valid_from <= now, Prediction.valid_until >= now
                )

            predictions = query.order_by(Prediction.created_at.desc()).all()
            return predictions

    def get_last_prediction_time(self, chart_id: int) -> Optional[datetime]:
        """Получить время последнего прогноза для карты"""
        with self.get_session() as session:
            last_prediction = (
                session.query(Prediction)
                .filter(Prediction.natal_chart_id == chart_id)
                .order_by(Prediction.created_at.desc())
                .first()
            )

            if last_prediction:
                return last_prediction.created_at
            return None

    def get_active_predictions_count(self, telegram_id: int) -> int:
        """Получить количество активных прогнозов пользователя"""
        with self.get_session() as session:
            now = datetime.utcnow()

            count = (
                session.query(Prediction)
                .join(User)
                .filter(
                    User.telegram_id == telegram_id,
                    Prediction.valid_from <= now,
                    Prediction.valid_until >= now,
                )
                .count()
            )

            return count

    def cleanup_expired_predictions(self) -> int:
        """Удалить истекшие прогнозы (для очистки БД)"""
        with self.get_session() as session:
            now = datetime.utcnow()

            expired_count = (
                session.query(Prediction).filter(Prediction.valid_until < now).count()
            )

            session.query(Prediction).filter(Prediction.valid_until < now).delete()

            session.commit()
            return expired_count

    def save_compatibility_report(
        self,
        user_id: int,
        user_name: str,
        partner_name: str,
        user_birth_date: datetime,
        partner_birth_date: datetime,
        sphere: str,
        report_text: str,
    ) -> CompatibilityReport:
        """Сохраняет отчет о совместимости в базу данных."""
        with self.get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                raise ValueError("Пользователь не найден")

            new_report = CompatibilityReport(
                user_id=user_id,
                user_name=user_name,
                partner_name=partner_name,
                user_birth_date=user_birth_date,
                partner_birth_date=partner_birth_date,
                sphere=sphere,
                report_text=report_text,
            )
            session.add(new_report)
            session.commit()
            session.refresh(new_report)
            return new_report

    def get_user_compatibility_reports(self, user_id: int) -> List[CompatibilityReport]:
        """Получает все отчеты о совместимости для пользователя."""
        with self.get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return []
            reports = (
                session.query(CompatibilityReport)
                .filter_by(user_id=user_id)
                .order_by(CompatibilityReport.created_at.desc())
                .all()
            )
            return reports

    def get_compatibility_report_by_id(
        self, report_id: int, user_id: int
    ) -> Optional[CompatibilityReport]:
        """Получает отчет о совместимости по ID с проверкой владельца."""
        with self.get_session() as session:
            report = (
                session.query(CompatibilityReport)
                .filter_by(id=report_id, user_id=user_id)
                .first()
            )
            return report

    def delete_compatibility_report(self, report_id: int, user_id: int) -> bool:
        """Удаляет отчет о совместимости по ID с проверкой владельца."""
        with self.get_session() as session:
            report = (
                session.query(CompatibilityReport)
                .filter_by(id=report_id, user_id=user_id)
                .first()
            )
            if report:
                session.delete(report)
                session.commit()
                return True
            return False

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПОДПИСКАМИ ===

    def get_or_create_subscription(self, telegram_id: int) -> Subscription:
        """Получить или создать подписку для пользователя"""
        with self.get_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден")

            # Проверяем, есть ли уже подписка
            subscription = (
                session.query(Subscription)
                .filter(Subscription.user_id == user.id)
                .first()
            )

            if not subscription:
                # Создаем новую бесплатную подписку
                subscription = Subscription(
                    user_id=user.id,
                    subscription_type=SubscriptionType.FREE,
                    status=SubscriptionStatus.ACTIVE,
                )
                session.add(subscription)
                session.commit()
                session.refresh(subscription)

            return subscription

    def create_premium_subscription(
        self,
        telegram_id: int,
        duration_days: int = 30,
        payment_id: str = None,
        payment_amount: float = None,
    ) -> Subscription:
        """Создать или обновить премиум подписку"""
        with self.get_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден")

            # Получаем существующую подписку или создаем новую
            subscription = (
                session.query(Subscription)
                .filter(Subscription.user_id == user.id)
                .first()
            )

            if subscription:
                # Обновляем существующую подписку
                subscription.subscription_type = SubscriptionType.PREMIUM
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.start_date = datetime.utcnow()
                subscription.end_date = datetime.utcnow() + timedelta(
                    days=duration_days
                )
                subscription.payment_id = payment_id
                subscription.payment_amount = payment_amount
                subscription.updated_at = datetime.utcnow()
            else:
                # Создаем новую премиум подписку
                subscription = Subscription(
                    user_id=user.id,
                    subscription_type=SubscriptionType.PREMIUM,
                    status=SubscriptionStatus.ACTIVE,
                    start_date=datetime.utcnow(),
                    end_date=datetime.utcnow() + timedelta(days=duration_days),
                    payment_id=payment_id,
                    payment_amount=payment_amount,
                )
                session.add(subscription)

            session.commit()
            session.refresh(subscription)
            return subscription

    def cancel_subscription(self, telegram_id: int) -> bool:
        """Отменить подписку пользователя"""
        with self.get_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return False

            subscription = (
                session.query(Subscription)
                .filter(Subscription.user_id == user.id)
                .first()
            )
            if not subscription:
                return False

            subscription.status = SubscriptionStatus.CANCELLED
            subscription.updated_at = datetime.utcnow()

            session.commit()
            return True

    def get_subscription_info(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию о подписке пользователя"""
        with self.get_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return None

            subscription = (
                session.query(Subscription)
                .filter(Subscription.user_id == user.id)
                .first()
            )
            if not subscription:
                return None

            return {
                "type": subscription.subscription_type.value,
                "status": subscription.status.value,
                "is_active": subscription.is_active,
                "is_premium": subscription.subscription_type == SubscriptionType.PREMIUM
                and subscription.is_active,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
                "days_remaining": subscription.days_remaining,
                "payment_amount": subscription.payment_amount,
                "payment_currency": subscription.payment_currency,
            }

    def check_and_expire_subscriptions(self) -> int:
        """Проверить и отметить истекшие подписки"""
        with self.get_session() as session:
            now = datetime.utcnow()

            # Находим все активные подписки с истекшим сроком
            expired_subscriptions = (
                session.query(Subscription)
                .filter(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.end_date.isnot(None),
                    Subscription.end_date <= now,
                )
                .all()
            )

            count = 0
            for subscription in expired_subscriptions:
                subscription.status = SubscriptionStatus.EXPIRED
                subscription.updated_at = now
                count += 1

            if count > 0:
                session.commit()

            return count

    def get_subscription_stats(self) -> Dict[str, int]:
        """Получить статистику по подпискам"""
        with self.get_session() as session:
            stats = (
                session.query(
                    Subscription.subscription_type, func.count(Subscription.id)
                )
                .group_by(Subscription.subscription_type)
                .all()
            )

            return {str(k.name): v for k, v in stats}

    def get_app_statistics(self) -> Dict[str, int]:
        """Собирает общую статистику по приложению."""
        with self.get_session() as session:
            total_users = session.query(func.count(User.id)).scalar()

            today_start = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            seven_days_ago = today_start - timedelta(days=7)
            thirty_days_ago = today_start - timedelta(days=30)

            new_users_today = (
                session.query(func.count(User.id))
                .filter(User.created_at >= today_start)
                .scalar()
            )
            new_users_7_days = (
                session.query(func.count(User.id))
                .filter(User.created_at >= seven_days_ago)
                .scalar()
            )
            new_users_30_days = (
                session.query(func.count(User.id))
                .filter(User.created_at >= thirty_days_ago)
                .scalar()
            )

            active_premium = (
                session.query(func.count(Subscription.id))
                .filter(
                    Subscription.subscription_type == SubscriptionType.PREMIUM,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    (Subscription.end_date == None)
                    | (Subscription.end_date > datetime.utcnow()),
                )
                .scalar()
            )

            total_charts = session.query(func.count(NatalChart.id)).scalar()

            return {
                "total_users": total_users,
                "users_today": new_users_today,
                "users_last_7_days": new_users_7_days,
                "users_last_30_days": new_users_30_days,
                "new_users_today": new_users_today,
                "new_users_7_days": new_users_7_days,
                "new_users_30_days": new_users_30_days,
                "active_premium": active_premium,
                "total_charts": total_charts,
                "total_natal_charts": total_charts,
            }

    # === РАСШИРЕННЫЕ МЕТОДЫ ДЛЯ АДМИН-ПАНЕЛИ ===

    def get_users_paginated(
        self, page: int = 1, per_page: int = 10, user_type: str = "all"
    ) -> tuple[List[User], int]:
        """Получить пользователей с пагинацией."""
        with self.get_session() as session:
            query = session.query(User).options(joinedload(User.subscription))

            if user_type == "premium":
                query = query.join(Subscription).filter(
                    Subscription.subscription_type == SubscriptionType.PREMIUM,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    (Subscription.end_date == None)
                    | (Subscription.end_date > datetime.utcnow()),
                )
            elif user_type == "active":
                # Пользователи с активностью за последние 7 дней
                week_ago = datetime.utcnow() - timedelta(days=7)
                query = query.filter(User.created_at >= week_ago)

            total_count = query.count()
            total_pages = (total_count + per_page - 1) // per_page

            users = query.offset((page - 1) * per_page).limit(per_page).all()
            return users, total_pages

    def get_premium_users(self) -> List[User]:
        """Получить всех пользователей с активной Premium подпиской."""
        with self.get_session() as session:
            users = (
                session.query(User)
                .options(joinedload(User.subscription))
                .join(Subscription)
                .filter(
                    Subscription.subscription_type == SubscriptionType.PREMIUM,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    (Subscription.end_date == None)
                    | (Subscription.end_date > datetime.utcnow()),
                )
                .all()
            )
            return users

    def get_expiring_subscriptions(self, days: int = 7) -> List[User]:
        """Получить пользователей с истекающими подписками."""
        with self.get_session() as session:
            cutoff_date = datetime.utcnow() + timedelta(days=days)
            users = (
                session.query(User)
                .options(joinedload(User.subscription))
                .join(Subscription)
                .filter(
                    Subscription.subscription_type == SubscriptionType.PREMIUM,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.end_date.isnot(None),
                    Subscription.end_date <= cutoff_date,
                    Subscription.end_date > datetime.utcnow(),
                )
                .all()
            )
            return users

    def get_user_activity(self, telegram_id: int) -> Dict[str, Any]:
        """Получить детальную информацию об активности пользователя."""
        with self.get_session() as session:
            user = (
                session.query(User)
                .options(
                    joinedload(User.subscription),
                    joinedload(User.natal_charts),
                    joinedload(User.predictions),
                )
                .filter(User.telegram_id == telegram_id)
                .first()
            )

            if not user:
                return {}

            return {
                "charts_count": len(user.natal_charts),
                "predictions_count": len(user.predictions),
                "last_chart_date": (
                    user.natal_charts[-1].created_at if user.natal_charts else None
                ),
                "last_prediction_date": (
                    user.predictions[-1].created_at if user.predictions else None
                ),
                "registration_date": user.created_at,
                "profile_complete": user.is_profile_complete,
                "notifications_enabled": user.notifications_enabled,
            }

    def get_detailed_statistics(self) -> Dict[str, Any]:
        """Получить подробную статистику системы."""
        with self.get_session() as session:
            # Базовая статистика
            total_users = session.query(func.count(User.id)).scalar()
            total_charts = session.query(func.count(NatalChart.id)).scalar()
            total_predictions = session.query(func.count(Prediction.id)).scalar()

            # Статистика по дням
            today_start = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            yesterday_start = today_start - timedelta(days=1)
            week_ago = today_start - timedelta(days=7)
            month_ago = today_start - timedelta(days=30)

            new_users_today = (
                session.query(func.count(User.id))
                .filter(User.created_at >= today_start)
                .scalar()
            )
            new_users_yesterday = (
                session.query(func.count(User.id))
                .filter(
                    User.created_at >= yesterday_start, User.created_at < today_start
                )
                .scalar()
            )
            new_users_week = (
                session.query(func.count(User.id))
                .filter(User.created_at >= week_ago)
                .scalar()
            )
            new_users_month = (
                session.query(func.count(User.id))
                .filter(User.created_at >= month_ago)
                .scalar()
            )

            # Статистика подписок
            active_premium = (
                session.query(func.count(Subscription.id))
                .filter(
                    Subscription.subscription_type == SubscriptionType.PREMIUM,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    (Subscription.end_date == None)
                    | (Subscription.end_date > datetime.utcnow()),
                )
                .scalar()
            )

            expired_premium = (
                session.query(func.count(Subscription.id))
                .filter(
                    Subscription.subscription_type == SubscriptionType.PREMIUM,
                    Subscription.status == SubscriptionStatus.EXPIRED,
                )
                .scalar()
            )

            # Активность
            charts_today = (
                session.query(func.count(NatalChart.id))
                .filter(NatalChart.created_at >= today_start)
                .scalar()
            )
            charts_week = (
                session.query(func.count(NatalChart.id))
                .filter(NatalChart.created_at >= week_ago)
                .scalar()
            )

            predictions_today = (
                session.query(func.count(Prediction.id))
                .filter(Prediction.created_at >= today_start)
                .scalar()
            )
            predictions_week = (
                session.query(func.count(Prediction.id))
                .filter(Prediction.created_at >= week_ago)
                .scalar()
            )

            return {
                "users": {
                    "total": total_users,
                    "today": new_users_today,
                    "yesterday": new_users_yesterday,
                    "week": new_users_week,
                    "month": new_users_month,
                },
                "subscriptions": {
                    "active_premium": active_premium,
                    "expired_premium": expired_premium,
                    "conversion_rate": (
                        round((active_premium / total_users * 100), 2)
                        if total_users > 0
                        else 0
                    ),
                },
                "content": {
                    "total_charts": total_charts,
                    "charts_today": charts_today,
                    "charts_week": charts_week,
                    "total_predictions": total_predictions,
                    "predictions_today": predictions_today,
                    "predictions_week": predictions_week,
                },
            }

    def bulk_extend_premium(self, user_ids: List[int], days: int) -> int:
        """Массовое продление Premium подписки."""
        with self.get_session() as session:
            count = 0
            for user_id in user_ids:
                user = session.query(User).filter(User.telegram_id == user_id).first()
                if user and user.subscription:
                    sub = user.subscription
                    if (
                        sub.subscription_type == SubscriptionType.PREMIUM
                        and sub.is_active
                    ):
                        if sub.end_date:
                            sub.end_date += timedelta(days=days)
                        else:
                            sub.end_date = datetime.utcnow() + timedelta(days=days)
                        count += 1

            if count > 0:
                session.commit()
            return count

    def cleanup_database(self) -> Dict[str, int]:
        """Очистка базы данных от устаревших данных."""
        with self.get_session() as session:
            # Удаляем истекшие прогнозы старше 30 дней
            month_ago = datetime.utcnow() - timedelta(days=30)
            expired_predictions = (
                session.query(Prediction)
                .filter(Prediction.valid_until < month_ago)
                .delete()
            )

            # Обновляем статус истекших подписок
            expired_subs = (
                session.query(Subscription)
                .filter(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.end_date.isnot(None),
                    Subscription.end_date <= datetime.utcnow(),
                )
                .all()
            )

            for sub in expired_subs:
                sub.status = SubscriptionStatus.EXPIRED
                sub.updated_at = datetime.utcnow()

            session.commit()

            return {
                "expired_predictions_removed": expired_predictions,
                "subscriptions_expired": len(expired_subs),
            }


# Создаем единственный экземпляр менеджера базы данных
db_manager = DatabaseManager()
