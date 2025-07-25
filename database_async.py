"""
Асинхронная версия DatabaseManager для улучшения производительности бота.
Использует aiosqlite и SQLAlchemy async для неблокирующих операций.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload

from database import (
    User,
    NatalChart,
    Prediction,
    Subscription,
    SubscriptionStatus,
    SubscriptionType,
    CompatibilityReport,
    Base,
)

logger = logging.getLogger(__name__)


def with_db_session(func):
    """
    Декоратор для автоматического управления сессиями БД.
    Применяет принцип DRY - избавляет от повторяющегося кода создания сессий.
    
    Использование:
    @with_db_session
    async def my_method(self, user_id: int) -> User:
        # self.session уже доступна
        result = await self.session.execute(select(User).where(User.telegram_id == user_id))
        return result.scalar_one_or_none()
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        async with self.get_session() as session:
            # Временно заменяем session в self
            original_session = getattr(self, '_session', None)
            self._session = session
            
            try:
                result = await func(self, *args, **kwargs)
                return result
            finally:
                # Восстанавливаем оригинальную сессию если была
                if original_session is not None:
                    self._session = original_session
                else:
                    delattr(self, '_session')
    
    return wrapper


@asynccontextmanager
async def db_session_context(db_manager):
    """
    Контекстный менеджер для работы с сессиями БД.
    Альтернатива декоратору для случаев, когда нужен более явный контроль.
    
    Использование:
    async with db_session_context(db_manager) as session:
        result = await session.execute(select(User))
        return result.scalars().all()
    """
    async with db_manager.get_session() as session:
        yield session


class AsyncDatabaseManager:
    """Асинхронный менеджер базы данных с применением принципа DRY"""

    def __init__(self, database_url: str = None):
        from config import Config
        
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = None
        self.session_factory = None
        self._session = None
        self.db_config = Config.get_database_config()

    async def init_db(self):
        """Инициализация базы данных"""
        self.engine = create_async_engine(
            self.database_url,
            **self.db_config
        )
        
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info(f"✅ Асинхронная база данных инициализирована: {self.database_url}")

    @asynccontextmanager
    async def get_session(self):
        """Контекстный менеджер для получения сессии БД"""
        if not self.session_factory:
            raise RuntimeError("База данных не инициализирована. Вызовите init_db()")
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # === ПОЛЬЗОВАТЕЛИ ===

    @with_db_session
    async def get_or_create_user(self, telegram_id: int, name: str) -> Tuple[User, bool]:
        """Получить или создать пользователя"""
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            return user, False
        
        user = User(telegram_id=telegram_id, name=name)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        
        logger.info(f"✅ Пользователь создан: {user.name} (ID: {user.telegram_id})")
        return user, True

    @with_db_session
    async def get_user_profile(self, telegram_id: int) -> Optional[User]:
        """Получить профиль пользователя с подгруженной подпиской"""
        from sqlalchemy.orm import selectinload
        result = await self._session.execute(
            select(User).options(selectinload(User.subscription)).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    @with_db_session
    async def set_notifications(self, telegram_id: int, enabled: bool) -> bool:
        """Включить или выключить уведомления для пользователя"""
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.notifications_enabled = enabled
            await self._session.flush()
            logger.info(f"✅ Уведомления {'включены' if enabled else 'выключены'} для пользователя {telegram_id}")
            return True
        return False

    @with_db_session
    async def update_user_profile(
        self,
        telegram_id: int,
        name: str,
        gender: str,
        birth_year: int,
        birth_city: str,
        birth_date: datetime,
        birth_time_specified: bool = True,
    ) -> Optional[User]:
        """Обновить профиль пользователя"""
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        user.name = name
        user.gender = gender
        user.birth_year = birth_year
        user.birth_city = birth_city
        user.birth_date = birth_date
        user.birth_time_specified = birth_time_specified
        user.is_profile_complete = True
        
        await self._session.flush()
        await self._session.refresh(user)
        
        logger.info(f"✅ Профиль обновлен: {user.name}")
        return user

    @with_db_session
    async def delete_user_data(self, telegram_id: int) -> bool:
        """Удалить все данные пользователя"""
        # Получаем пользователя
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Удаляем связанные данные
        await self._session.execute(
            delete(Prediction).where(Prediction.telegram_id == telegram_id)
        )
        await self._session.execute(
            delete(NatalChart).where(NatalChart.telegram_id == telegram_id)
        )
        await self._session.execute(
            delete(CompatibilityReport).where(CompatibilityReport.user_id == user.id)
        )
        await self._session.execute(
            delete(Subscription).where(Subscription.telegram_id == telegram_id)
        )
        
        # Удаляем пользователя
        await self._session.delete(user)
        
        logger.info(f"✅ Данные пользователя {telegram_id} удалены")
        return True

    # === НАТАЛЬНЫЕ КАРТЫ ===

    @with_db_session
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
        planets_data: Dict[str, Dict[str, Union[str, float]]],
        chart_type: str = "own",
        chart_owner_name: str = None,
    ) -> NatalChart:
        """Создать натальную карту"""
        # Получаем пользователя
        user_result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден")
        
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

        if planets_data:
            # Проверяем, являются ли данные датаклассами и конвертируем в dict
            first_value = next(iter(planets_data.values()), None)
            if first_value and is_dataclass(first_value):
                planets_data_dict = {
                    name: asdict(pos) for name, pos in planets_data.items()
                }
                chart.set_planets_data(planets_data_dict)
            else:
                # Если это уже dict или что-то другое, сохраняем как есть
                chart.set_planets_data(planets_data)
        else:
            chart.set_planets_data({})
        
        self._session.add(chart)
        await self._session.flush()
        await self._session.refresh(chart)
        
        logger.info(f"✅ Натальная карта создана: {name}")
        return chart

    @with_db_session
    async def get_user_charts(self, telegram_id: int) -> List[NatalChart]:
        """Получить натальные карты пользователя"""
        result = await self._session.execute(
            select(NatalChart)
            .join(User)
            .where(User.telegram_id == telegram_id)
            .order_by(NatalChart.created_at.desc())
        )
        return list(result.scalars().all())

    @with_db_session
    async def get_chart_by_id(self, chart_id: int, telegram_id: int) -> Optional[NatalChart]:
        """Получить натальную карту по ID"""
        result = await self._session.execute(
            select(NatalChart)
            .join(User)
            .where(
                and_(NatalChart.id == chart_id, User.telegram_id == telegram_id)
            )
        )
        return result.scalar_one_or_none()

    @with_db_session
    async def delete_chart(self, chart_id: int, telegram_id: int) -> bool:
        """Удалить натальную карту"""
        result = await self._session.execute(
            select(NatalChart)
            .join(User)
            .where(
                and_(NatalChart.id == chart_id, User.telegram_id == telegram_id)
            )
        )
        chart = result.scalar_one_or_none()
        
        if not chart:
            return False
        
        await self._session.delete(chart)
        logger.info(f"✅ Натальная карта {chart_id} удалена")
        return True

    # === ПРОГНОЗЫ ===

    @with_db_session
    async def create_prediction(
        self,
        telegram_id: int,
        chart_id: int,
        prediction_type: str,
        valid_from: datetime,
        valid_until: datetime,
        content: str,
        generation_time: float = 0.0,
    ) -> Prediction:
        """Создать прогноз"""
        # Получаем пользователя
        user_result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден")
        
        prediction = Prediction(
            user_id=user.id,
            natal_chart_id=chart_id,
            prediction_type=prediction_type,
            valid_from=valid_from,
            valid_until=valid_until,
            content=content,
            generation_time=generation_time,
        )
        
        self._session.add(prediction)
        await self._session.flush()
        await self._session.refresh(prediction)
        
        logger.info(f"✅ Прогноз создан: {prediction.prediction_type}")
        return prediction

    @with_db_session
    async def find_valid_prediction(
        self, telegram_id: int, chart_id: int, prediction_type: str
    ) -> Optional[Prediction]:
        """Найти действующий прогноз"""
        now = datetime.utcnow()
        result = await self._session.execute(
            select(Prediction)
            .join(User)
            .where(
                and_(
                    User.telegram_id == telegram_id,
                    Prediction.natal_chart_id == chart_id,
                    Prediction.prediction_type == prediction_type,
                    Prediction.valid_from <= now,
                    Prediction.valid_until >= now,
                )
            )
        )
        return result.scalar_one_or_none()

    @with_db_session
    async def get_user_predictions(self, telegram_id: int) -> List[Prediction]:
        """Получить прогнозы пользователя"""
        result = await self._session.execute(
            select(Prediction)
            .join(User)
            .where(User.telegram_id == telegram_id)
            .order_by(Prediction.created_at.desc())
        )
        return list(result.scalars().all())

    # === ПОДПИСКИ ===

    @with_db_session
    async def get_or_create_subscription(self, telegram_id: int) -> Subscription:
        """Получить или создать подписку пользователя"""
        # Получаем пользователя
        user_result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден")
        
        result = await self._session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            return subscription
        
        subscription = Subscription(
            user_id=user.id,
            subscription_type=SubscriptionType.FREE,
            status=SubscriptionStatus.ACTIVE,
        )
        
        self._session.add(subscription)
        await self._session.flush()
        await self._session.refresh(subscription)
        
        logger.info(f"✅ Подписка создана для пользователя {telegram_id}")
        return subscription

    @with_db_session
    async def get_subscription_info(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию о подписке пользователя"""
        user_result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return None
        
        subscription_result = await self._session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = subscription_result.scalar_one_or_none()
        
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

    @with_db_session
    async def create_premium_subscription(
        self, telegram_id: int, duration_days: int = 30, payment_id: str = None, payment_amount: float = None
    ) -> Subscription:
        """Создать Premium подписку"""
        # Получаем пользователя
        user_result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден")
        
        # Удаляем существующую подписку если есть
        await self._session.execute(
            delete(Subscription).where(Subscription.user_id == user.id)
        )
        
        subscription = Subscription(
            user_id=user.id,
            subscription_type=SubscriptionType.PREMIUM,
            status=SubscriptionStatus.ACTIVE,
            end_date=datetime.utcnow() + timedelta(days=duration_days),
            payment_id=payment_id,
            payment_amount=payment_amount,
            payment_currency="RUB",
        )
        
        self._session.add(subscription)
        await self._session.flush()
        await self._session.refresh(subscription)
        
        logger.info(f"✅ Premium подписка создана для {telegram_id} на {duration_days} дней")
        return subscription

    @with_db_session
    async def revoke_premium_subscription(self, telegram_id: int) -> bool:
        """Отозвать Premium подписку"""
        # Получаем пользователя
        user_result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return False
        
        result = await self._session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return False
        
        subscription.subscription_type = SubscriptionType.FREE
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.end_date = None
        
        logger.info(f"✅ Premium подписка отозвана у пользователя {telegram_id}")
        return True

    @with_db_session
    async def cancel_premium_subscription(self, telegram_id: int) -> bool:
        """Отменить Premium подписку (алиас для revoke_premium_subscription)"""
        return await self.revoke_premium_subscription(telegram_id)

    # === СОВМЕСТИМОСТЬ ===

    @with_db_session
    async def get_user_compatibility_reports(self, user_id: int) -> List[CompatibilityReport]:
        """Получить отчеты по совместимости пользователя"""
        result = await self._session.execute(
            select(CompatibilityReport)
            .where(CompatibilityReport.user_id == user_id)
            .order_by(CompatibilityReport.created_at.desc())
        )
        return list(result.scalars().all())

    @with_db_session
    async def save_compatibility_report(
        self,
        user_id: int,
        user_name: str,
        partner_name: str,
        user_birth_date: datetime,
        partner_birth_date: datetime,
        sphere: str,
        report_text: str,
    ) -> CompatibilityReport:
        """Сохранить отчет по совместимости"""
        report = CompatibilityReport(
            user_id=user_id,
            user_name=user_name,
            partner_name=partner_name,
            user_birth_date=user_birth_date,
            partner_birth_date=partner_birth_date,
            sphere=sphere,
            report_text=report_text,
        )
        self._session.add(report)
        await self._session.flush()
        await self._session.refresh(report)
        return report

    @with_db_session
    async def get_compatibility_report_by_id(
        self, report_id: int, user_id: int
    ) -> Optional[CompatibilityReport]:
        """Получить отчет о совместимости по ID с проверкой владельца"""
        result = await self._session.execute(
            select(CompatibilityReport).where(
                and_(
                    CompatibilityReport.id == report_id,
                    CompatibilityReport.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    @with_db_session
    async def delete_compatibility_report(self, report_id: int, user_id: int) -> bool:
        """Удалить отчет о совместимости по ID с проверкой владельца"""
        result = await self._session.execute(
            select(CompatibilityReport).where(
                and_(
                    CompatibilityReport.id == report_id,
                    CompatibilityReport.user_id == user_id
                )
            )
        )
        report = result.scalar_one_or_none()
        
        if report:
            await self._session.delete(report)
            await self._session.flush()
            logger.info(f"✅ Отчет о совместимости {report_id} удален")
            return True
        return False

    # === АДМИН ФУНКЦИИ ===

    @with_db_session
    async def get_users_paginated(
        self, page: int = 1, per_page: int = 20, filter_type: str = "all"
    ) -> Tuple[List[User], int]:
        """Получить пользователей с пагинацией"""
        offset = (page - 1) * per_page
        
        # Базовый запрос
        base_query = select(User).options(selectinload(User.subscription))
        
        # Применяем фильтры
        if filter_type == "premium":
            base_query = base_query.join(Subscription).where(
                Subscription.subscription_type == SubscriptionType.PREMIUM
            )
        elif filter_type == "free":
            base_query = base_query.join(Subscription).where(
                Subscription.subscription_type == SubscriptionType.FREE
            )
        elif filter_type == "active":
            base_query = base_query.where(User.last_activity >= datetime.utcnow() - timedelta(days=7))
        
        # Общее количество
        count_result = await self._session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total_count = count_result.scalar()
        
        # Данные с пагинацией
        result = await self._session.execute(
            base_query.offset(offset).limit(per_page)
        )
        users = list(result.scalars().all())
        
        return users, total_count

    @with_db_session
    async def get_users_for_mailing(self) -> List[User]:
        """Получить пользователей для рассылки"""
        result = await self._session.execute(
            select(User)
            .where(User.notifications_enabled == True)
            .options(selectinload(User.subscription))
        )
        users = list(result.scalars().all())
        logger.info(f"📋 get_users_for_mailing: найдено {len(users)} пользователей с включенными уведомлениями")
        
        # Логируем детали пользователей для отладки
        for user in users:
            logger.info(f"👤 Пользователь для рассылки: ID={user.telegram_id}, имя='{user.name}', уведомления={user.notifications_enabled}")
        
        return users

    @with_db_session
    async def get_expiring_subscriptions(self, days: int = 7) -> List[User]:
        """Получить пользователей с истекающими подписками"""
        expiry_date = datetime.utcnow() + timedelta(days=days)
        result = await self._session.execute(
            select(User)
            .join(Subscription)
            .where(
                and_(
                    Subscription.subscription_type == SubscriptionType.PREMIUM,
                    Subscription.end_date <= expiry_date,
                    Subscription.end_date > datetime.utcnow(),
                )
            )
        )
        return list(result.scalars().all())

    @with_db_session
    async def bulk_extend_premium(self, telegram_ids: List[int], days: int) -> int:
        """Массовое продление Premium подписок"""
        count = 0
        for telegram_id in telegram_ids:
            # Получаем пользователя
            user_result = await self._session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                continue
                
            result = await self._session.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
            subscription = result.scalar_one_or_none()
            
            if subscription and subscription.subscription_type == SubscriptionType.PREMIUM:
                if subscription.end_date:
                    subscription.end_date += timedelta(days=days)
                else:
                    subscription.end_date = datetime.utcnow() + timedelta(days=days)
                count += 1
        
        logger.info(f"✅ Продлено {count} Premium подписок")
        return count

    @with_db_session
    async def check_and_expire_subscriptions(self) -> int:
        """Проверить и истечь просроченные подписки"""
        result = await self._session.execute(
            update(Subscription)
            .where(
                and_(
                    Subscription.subscription_type == SubscriptionType.PREMIUM,
                    Subscription.end_date < datetime.utcnow(),
                    Subscription.status == SubscriptionStatus.ACTIVE,
                )
            )
            .values(status=SubscriptionStatus.EXPIRED)
        )
        
        count = result.rowcount
        logger.info(f"✅ Истекло {count} подписок")
        return count

    @with_db_session
    async def get_app_statistics(self) -> Dict[str, int]:
        """Получить статистику приложения"""
        # Общее количество пользователей
        total_users_result = await self._session.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        # Новые пользователи сегодня
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_users_result = await self._session.execute(
            select(func.count(User.id)).where(User.created_at >= today_start)
        )
        new_users_today = today_users_result.scalar()
        
        # Новые пользователи за 7 дней
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_users_result = await self._session.execute(
            select(func.count(User.id)).where(User.created_at >= week_ago)
        )
        new_users_7_days = week_users_result.scalar()
        
        # Новые пользователи за 30 дней
        month_ago = datetime.utcnow() - timedelta(days=30)
        month_users_result = await self._session.execute(
            select(func.count(User.id)).where(User.created_at >= month_ago)
        )
        new_users_30_days = month_users_result.scalar()
        
        # Активные Premium подписки
        active_premium_result = await self._session.execute(
            select(func.count(Subscription.id)).where(
                and_(
                    Subscription.subscription_type == SubscriptionType.PREMIUM,
                    or_(
                        Subscription.end_date > datetime.utcnow(),
                        Subscription.end_date.is_(None)
                    ),
                    Subscription.status == SubscriptionStatus.ACTIVE,
                )
            )
        )
        active_premium = active_premium_result.scalar()
        
        # Общее количество натальных карт
        total_charts_result = await self._session.execute(select(func.count(NatalChart.id)))
        total_charts = total_charts_result.scalar()
        
        return {
            "total_users": total_users,
            "new_users_today": new_users_today,
            "new_users_7_days": new_users_7_days,
            "new_users_30_days": new_users_30_days,
            "active_premium": active_premium,
            "total_charts": total_charts,
        }

    @with_db_session
    async def get_detailed_statistics(self) -> Dict[str, int]:
        """Получить детальную статистику для админ-панели"""
        # Общее количество пользователей
        total_users_result = await self._session.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        # Пользователи с завершенным профилем
        complete_profiles_result = await self._session.execute(
            select(func.count(User.id)).where(User.is_profile_complete == True)
        )
        complete_profiles = complete_profiles_result.scalar()
        
        # Активные Premium подписки
        active_premium_result = await self._session.execute(
            select(func.count(Subscription.id)).where(
                and_(
                    Subscription.subscription_type == SubscriptionType.PREMIUM,
                    or_(
                        Subscription.end_date > datetime.utcnow(),
                        Subscription.end_date.is_(None)
                    ),
                    Subscription.status == SubscriptionStatus.ACTIVE,
                )
            )
        )
        active_premium = active_premium_result.scalar()
        
        # Общее количество натальных карт
        total_charts_result = await self._session.execute(select(func.count(NatalChart.id)))
        total_charts = total_charts_result.scalar()
        
        # Общее количество прогнозов
        total_predictions_result = await self._session.execute(select(func.count(Prediction.id)))
        total_predictions = total_predictions_result.scalar()
        
        return {
            "total_users": total_users,
            "complete_profiles": complete_profiles,
            "active_premium": active_premium,
            "total_charts": total_charts,
            "total_predictions": total_predictions,
        }

    @with_db_session
    async def get_subscription_stats(self) -> Dict[str, int]:
        """Получить статистику по подпискам"""
        # Общее количество пользователей
        total_users_result = await self._session.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        # Бесплатные пользователи
        free_users_result = await self._session.execute(
            select(func.count(Subscription.id)).where(
                Subscription.subscription_type == SubscriptionType.FREE
            )
        )
        total_free = free_users_result.scalar()
        
        # Premium пользователи
        premium_users_result = await self._session.execute(
            select(func.count(Subscription.id)).where(
                Subscription.subscription_type == SubscriptionType.PREMIUM
            )
        )
        total_premium = premium_users_result.scalar()
        
        # Активные Premium подписки
        active_premium_result = await self._session.execute(
            select(func.count(Subscription.id)).where(
                and_(
                    Subscription.subscription_type == SubscriptionType.PREMIUM,
                    or_(
                        Subscription.expires_at > datetime.utcnow(),
                        Subscription.expires_at.is_(None)
                    ),
                    Subscription.status == SubscriptionStatus.ACTIVE,
                )
            )
        )
        active_premium = active_premium_result.scalar()
        
        return {
            "total_users": total_users,
            "total_free": total_free,
            "total_premium": total_premium,
            "active_premium": active_premium,
        }

    @with_db_session
    async def get_total_users_count(self) -> int:
        """Получить общее количество пользователей"""
        result = await self._session.execute(select(func.count(User.id)))
        return result.scalar()

    @with_db_session
    async def get_user_activity(self, user_id: int) -> Dict[str, int]:
        """Получить активность пользователя"""
        # user_id здесь — это telegram_id, нужно получить внутренний id пользователя
        user_result = await self._session.execute(select(User).where(User.telegram_id == user_id))
        user_obj = user_result.scalar_one_or_none()
        if not user_obj:
            return {}
        real_user_id = user_obj.id

        # Количество натальных карт
        charts_result = await self._session.execute(
            select(func.count(NatalChart.id)).where(NatalChart.user_id == real_user_id)
        )
        charts_count = charts_result.scalar()
        # Количество прогнозов
        predictions_result = await self._session.execute(
            select(func.count(Prediction.id)).where(Prediction.user_id == real_user_id)
        )
        predictions_count = predictions_result.scalar()
        # Количество отчетов о совместимости
        reports_result = await self._session.execute(
            select(func.count(CompatibilityReport.id)).where(CompatibilityReport.user_id == real_user_id)
        )
        reports_count = reports_result.scalar()
        return {
            "charts_count": charts_count,
            "predictions_count": predictions_count,
            "reports_count": reports_count,
            "registration_date": user_obj.created_at,
            "profile_complete": user_obj.is_profile_complete,
            "notifications_enabled": user_obj.notifications_enabled,
            "last_chart_date": None,
            "last_prediction_date": None,
        }

    @with_db_session
    async def cleanup_database(self) -> Dict[str, int]:
        """Очистка базы данных от устаревших данных"""
        # Удаляем старые прогнозы (старше 30 дней)
        month_ago = datetime.utcnow() - timedelta(days=30)
        old_predictions_result = await self._session.execute(
            delete(Prediction).where(Prediction.created_at < month_ago)
        )
        deleted_predictions = old_predictions_result.rowcount
        
        # Удаляем старые отчеты о совместимости (старше 90 дней)
        three_months_ago = datetime.utcnow() - timedelta(days=90)
        old_reports_result = await self._session.execute(
            delete(CompatibilityReport).where(CompatibilityReport.created_at < three_months_ago)
        )
        deleted_reports = old_reports_result.rowcount
        
        await self._session.commit()
        
        return {
            "deleted_predictions": deleted_predictions,
            "deleted_reports": deleted_reports,
        }

    async def close(self):
        """Закрыть соединение с базой данных"""
        if self.engine:
            await self.engine.dispose()
            logger.info("✅ Соединение с базой данных закрыто")


# Глобальный экземпляр для использования в приложении
async_db_manager = AsyncDatabaseManager()
