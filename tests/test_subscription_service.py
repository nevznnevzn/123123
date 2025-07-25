from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from models import PlanetPosition
from services.subscription_service import SubscriptionService


class TestSubscriptionService:
    """Тесты для сервиса подписки"""

    def test_init_creates_service(self):
        """Тест: инициализация создает сервис"""
        service = SubscriptionService()
        assert service is not None
        assert hasattr(service, "FREE_USER_LIMITS")
        assert hasattr(service, "SUBSCRIPTION_PRICES")

    @patch("services.subscription_service.db_manager")
    def test_get_user_subscription_status_premium(self, mock_db_manager):
        """Тест: получение статуса премиум пользователя"""
        # Настройка мока
        mock_subscription = Mock()
        mock_db_manager.get_or_create_subscription.return_value = mock_subscription
        mock_db_manager.get_subscription_info.return_value = {
            "type": "premium",
            "status": "active",
            "is_active": True,
            "is_premium": True,
            "days_remaining": 15,
        }

        service = SubscriptionService()
        status = service.get_user_subscription_status(123456)

        assert status["type"] == "premium"
        assert status["is_premium"] is True
        assert status["days_remaining"] == 15

    @patch("services.subscription_service.db_manager")
    def test_get_user_subscription_status_free(self, mock_db_manager):
        """Тест: получение статуса бесплатного пользователя"""
        # Настройка мока
        mock_subscription = Mock()
        mock_db_manager.get_or_create_subscription.return_value = mock_subscription
        mock_db_manager.get_subscription_info.return_value = {
            "type": "free",
            "status": "active",
            "is_active": True,
            "is_premium": False,
            "days_remaining": None,
        }

        service = SubscriptionService()
        status = service.get_user_subscription_status(123456)

        assert status["type"] == "free"
        assert status["is_premium"] is False
        assert status["days_remaining"] is None

    @patch("services.subscription_service.db_manager")
    def test_get_user_subscription_status_error_fallback(self, mock_db_manager):
        """Тест: fallback при ошибке получения подписки"""
        # Настройка мока для ошибки
        mock_db_manager.get_or_create_subscription.side_effect = Exception(
            "Database error"
        )

        service = SubscriptionService()
        status = service.get_user_subscription_status(123456)

        # Должен вернуть базовые настройки бесплатного пользователя
        assert status["type"] == "free"
        assert status["is_premium"] is False
        assert status["is_active"] is True

    @patch.object(SubscriptionService, "is_user_premium")
    async def test_filter_planets_for_premium_user(self, mock_is_premium):
        """Тест: фильтрация планет для премиум пользователя"""
        mock_is_premium.return_value = True

        planets = {
            "Солнце": PlanetPosition(sign="Овен", degree=15.0),
            "Луна": PlanetPosition(sign="Телец", degree=20.0),
            "Марс": PlanetPosition(sign="Близнецы", degree=25.0),
            "Венера": PlanetPosition(sign="Рак", degree=10.0),
        }

        service = SubscriptionService()
        filtered = await service.filter_planets_for_user(planets, 123456)

        # Премиум пользователи видят все планеты
        assert len(filtered) == 4
        assert "Марс" in filtered
        assert "Венера" in filtered

    @patch.object(SubscriptionService, "is_user_premium")
    async def test_filter_planets_for_free_user(self, mock_is_premium):
        """Тест: фильтрация планет для бесплатного пользователя"""
        mock_is_premium.return_value = False

        planets = {
            "Солнце": PlanetPosition(sign="Овен", degree=15.0),
            "Луна": PlanetPosition(sign="Телец", degree=20.0),
            "Асцендент": PlanetPosition(sign="Лев", degree=5.0),
            "Марс": PlanetPosition(sign="Близнецы", degree=25.0),
            "Венера": PlanetPosition(sign="Рак", degree=10.0),
        }

        service = SubscriptionService()
        filtered = await service.filter_planets_for_user(planets, 123456)

        # Бесплатные пользователи видят только основные планеты
        assert len(filtered) == 3
        assert "Солнце" in filtered
        assert "Луна" in filtered
        assert "Асцендент" in filtered
        assert "Марс" not in filtered
        assert "Венера" not in filtered

    @patch.object(SubscriptionService, "is_user_premium")
    @patch("services.subscription_service.db_manager")
    def test_can_create_natal_chart_premium(self, mock_db_manager, mock_is_premium):
        """Тест: премиум пользователь может создавать неограниченное количество карт"""
        mock_is_premium.return_value = True

        service = SubscriptionService()
        can_create, message = service.can_create_natal_chart(123456)

        assert can_create is True
        assert message == ""

    @patch.object(SubscriptionService, "is_user_premium")
    @patch("services.subscription_service.db_manager")
    def test_can_create_natal_chart_free_under_limit(
        self, mock_db_manager, mock_is_premium
    ):
        """Тест: бесплатный пользователь может создать карту если не достиг лимита"""
        mock_is_premium.return_value = False
        mock_db_manager.get_user_charts.return_value = []  # Нет карт

        service = SubscriptionService()
        can_create, message = service.can_create_natal_chart(123456)

        assert can_create is True
        assert message == ""

    @patch.object(SubscriptionService, "is_user_premium")
    @patch("services.subscription_service.db_manager")
    def test_can_create_natal_chart_free_over_limit(
        self, mock_db_manager, mock_is_premium
    ):
        """Тест: бесплатный пользователь не может создать карту если достиг лимита"""
        mock_is_premium.return_value = False
        mock_db_manager.get_user_charts.return_value = [Mock()]  # Одна карта (лимит)

        service = SubscriptionService()
        can_create, message = service.can_create_natal_chart(123456)

        assert can_create is False
        assert "Бесплатным пользователям доступна только 1 натальная карта" in message

    def test_get_subscription_offer_text(self):
        """Тест: получение текста предложения подписки"""
        service = SubscriptionService()
        text = service.get_subscription_offer_text(123456)

        assert "Premium подписка SolarBalance" in text
        assert "499 RUB" in text
        assert "Неограниченные вопросы" in text
        assert "Полная натальная карта" in text

    @patch("services.subscription_service.db_manager")
    def test_create_premium_subscription_success(self, mock_db_manager):
        """Тест: успешное создание премиум подписки"""
        mock_subscription = Mock()
        mock_db_manager.create_premium_subscription.return_value = mock_subscription

        service = SubscriptionService()
        result = service.create_premium_subscription(123456, "payment_123")

        assert result is True
        mock_db_manager.create_premium_subscription.assert_called_once_with(
            telegram_id=123456,
            duration_days=30,
            payment_id="payment_123",
            payment_amount=499,
        )

    @patch("services.subscription_service.db_manager")
    def test_create_premium_subscription_error(self, mock_db_manager):
        """Тест: ошибка при создании премиум подписки"""
        mock_db_manager.create_premium_subscription.side_effect = Exception(
            "Database error"
        )

        service = SubscriptionService()
        result = service.create_premium_subscription(123456)

        assert result is False

    @patch.object(SubscriptionService, "get_user_subscription_status")
    def test_get_subscription_status_text_premium(self, mock_get_status):
        """Тест: текст статуса для премиум пользователя"""
        mock_get_status.return_value = {"is_premium": True, "days_remaining": 15}

        service = SubscriptionService()
        text = service.get_subscription_status_text(123456)

        assert "Premium активна" in text
        assert "Осталось дней: 15" in text

    @patch.object(SubscriptionService, "get_user_subscription_status")
    def test_get_subscription_status_text_free(self, mock_get_status):
        """Тест: текст статуса для бесплатного пользователя"""
        mock_get_status.return_value = {"is_premium": False}

        service = SubscriptionService()
        text = service.get_subscription_status_text(123456)

        assert "Бесплатная версия" in text
        assert "Оформите Premium" in text


if __name__ == "__main__":
    pytest.main([__file__])
