import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database import SubscriptionStatus, SubscriptionType
from database_async import async_db_manager
from models import PlanetPosition

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Сервис для управления подписками"""

    # Конфигурация подписок
    SUBSCRIPTION_PRICES = {
        "monthly": {
            "price": 499,
            "currency": "RUB",
            "duration_days": 30,
            "description": "Месячная подписка",
        }
    }

    # Лимиты для бесплатных пользователей
    FREE_USER_LIMITS = {
        "natal_charts": 3,  # Три натальные карты
        "daily_questions": 5,  # 5 вопросов в день (всего)
        "planets_shown": ["Солнце", "Луна", "Асцендент"],  # Основные планеты + Асцендент
    }

    def __init__(self):
        pass

    async def get_user_subscription_status(self, telegram_id: int) -> Dict[str, Any]:
        """Получить статус подписки пользователя"""
        try:
            # Получаем или создаем подписку (по умолчанию FREE)
            subscription = await async_db_manager.get_or_create_subscription(telegram_id)

            subscription_info = await async_db_manager.get_subscription_info(telegram_id)
            if not subscription_info:
                # Если почему-то не удалось получить информацию, создаем базовую
                subscription_info = {
                    "type": "free",
                    "status": "active",
                    "is_active": True,
                    "is_premium": False,
                    "days_remaining": None,
                }

            return subscription_info

        except Exception as e:
            logger.error(f"Ошибка получения статуса подписки для {telegram_id}: {e}")
            # В случае ошибки возвращаем базовые настройки бесплатного пользователя
            return {
                "type": "free",
                "status": "active",
                "is_active": True,
                "is_premium": False,
                "days_remaining": None,
            }

    async def is_user_premium(self, telegram_id: int) -> bool:
        """Проверить, является ли пользователь премиум"""
        status = await self.get_user_subscription_status(telegram_id)
        return status.get("is_premium", False)

    async def filter_planets_for_user(
        self, planets: Dict[str, PlanetPosition], telegram_id: int
    ) -> Dict[str, PlanetPosition]:
        """Фильтрует планеты в зависимости от типа подписки"""
        if await self.is_user_premium(telegram_id):
            # Премиум пользователи видят все планеты
            return planets

        # Бесплатные пользователи видят только основные планеты
        filtered_planets = {}
        allowed_planets = self.FREE_USER_LIMITS["planets_shown"]

        for planet_name, position in planets.items():
            if planet_name in allowed_planets:
                filtered_planets[planet_name] = position

        return filtered_planets

    async def can_create_natal_chart(self, telegram_id: int) -> tuple[bool, str]:
        """Проверить, может ли пользователь создать новую натальную карту"""
        if await self.is_user_premium(telegram_id):
            return True, ""

        # Для бесплатных пользователей - ограничение на количество карт
        user_charts = await async_db_manager.get_user_charts(telegram_id)
        max_charts = self.FREE_USER_LIMITS["natal_charts"]

        if len(user_charts) >= max_charts:
            return (
                False,
                f"Бесплатным пользователям доступна только {max_charts} натальная карта. Оформите подписку для создания неограниченного количества карт.",
            )

        return True, ""

    def get_subscription_offer_text(self, telegram_id: int) -> str:
        """Получить текст предложения подписки"""
        monthly = self.SUBSCRIPTION_PRICES["monthly"]

        text = f"""
💎 <b>Premium подписка SolarBalance</b> ✨

🌟 <b>Что вы получите:</b>
• 🪐 <b>Полная натальная карта</b> - все планеты и аспекты
• 🔮 <b>Неограниченные вопросы</b> Звёздному совету
• 🌙 <b>Детальные транзиты</b> и прогнозы
• 📊 <b>Неограниченные натальные карты</b>
• 🏆 <b>Приоритетная обработка</b> запросов
• 🎯 <b>Персональные рекомендации</b>

💰 <b>Стоимость:</b> {monthly['price']} {monthly['currency']} в месяц

🎁 <b>Сейчас доступно:</b>
• 1 натальная карта (только Солнце, Луна, Асцендент)
• 5 вопросов в день

🚀 Готовы разблокировать полный потенциал астрологии?
"""
        return text.strip()

    async def create_premium_subscription(
        self, telegram_id: int, payment_id: str = None
    ) -> bool:
        """Создать премиум подписку для пользователя"""
        try:
            monthly = self.SUBSCRIPTION_PRICES["monthly"]
            subscription = await async_db_manager.create_premium_subscription(
                telegram_id=telegram_id,
                duration_days=monthly["duration_days"],
                payment_id=payment_id,
                payment_amount=monthly["price"],
            )

            logger.info(f"Создана премиум подписка для пользователя {telegram_id}")
            return True

        except Exception as e:
            logger.error(f"Ошибка создания премиум подписки для {telegram_id}: {e}")
            return False

    async def cancel_subscription(self, telegram_id: int) -> bool:
        """Отменить подписку пользователя"""
        try:
            result = await async_db_manager.cancel_premium_subscription(telegram_id)
            if result:
                logger.info(f"Подписка отменена для пользователя {telegram_id}")
            return result

        except Exception as e:
            logger.error(f"Ошибка отмены подписки для {telegram_id}: {e}")
            return False

    async def get_subscription_status_text(self, telegram_id: int) -> str:
        """Получить текст статуса подписки"""
        status = await self.get_user_subscription_status(telegram_id)

        if status["is_premium"]:
            days_remaining = status.get("days_remaining")
            if days_remaining is not None:
                return f"💎 <b>Premium активна</b>\n⏰ Осталось дней: {days_remaining}"
            else:
                return "💎 <b>Premium активна</b>\n♾️ Бессрочная подписка"
        else:
            return (
                "🆓 <b>Бесплатная версия</b>\n💎 Оформите Premium для полного доступа"
            )

    async def expire_subscriptions(self) -> int:
        """Проверить и отметить истекшие подписки"""
        return await async_db_manager.check_and_expire_subscriptions()

    async def get_admin_stats(self) -> Dict[str, Any]:
        """Получить статистику для администратора"""
        try:
            stats = await async_db_manager.get_subscription_stats()
            return {
                "total_users": stats["total_users"],
                "free_users": stats["total_free"],
                "premium_users": stats["total_premium"],
                "active_premium": stats["active_premium"],
                "conversion_rate": round(
                    (stats["active_premium"] / max(stats["total_users"], 1)) * 100, 2
                ),
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики подписок: {e}")
            return {
                "total_users": 0,
                "free_users": 0,
                "premium_users": 0,
                "active_premium": 0,
                "conversion_rate": 0.0,
            }
