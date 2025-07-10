"""
Тесты для асинхронной базы данных.
Проверяют корректность работы новой async реализации.
"""

from datetime import datetime, timedelta

import pytest

from database_async import (
    AsyncDatabaseManager,
    NatalChart,
    Subscription,
    SubscriptionType,
    User,
)


@pytest.mark.asyncio
@pytest.mark.database
class TestAsyncDatabaseManager:
    """Тесты для асинхронного менеджера базы данных"""

    async def test_create_and_get_user(self, test_db: AsyncDatabaseManager):
        """Тест создания и получения пользователя"""
        # Создаем пользователя
        user, created = await test_db.get_or_create_user(12345, "Test User")

        assert created is True
        assert user.telegram_id == 12345
        assert user.name == "Test User"
        assert user.is_profile_complete is False

        # Получаем существующего пользователя
        user2, created2 = await test_db.get_or_create_user(12345, "Updated Name")

        assert created2 is False
        assert user2.id == user.id
        assert user2.name == "Updated Name"  # Имя должно обновиться

    async def test_update_user_profile(self, test_db: AsyncDatabaseManager):
        """Тест обновления профиля пользователя"""
        # Создаем пользователя
        user, _ = await test_db.get_or_create_user(12345, "Test User")

        # Обновляем профиль
        updated_user = await test_db.update_user_profile(
            telegram_id=12345,
            gender="Мужской",
            birth_year=1990,
            birth_city="Moscow",
            birth_date=datetime(1990, 1, 1, 12, 0),
        )

        assert updated_user is not None
        assert updated_user.gender == "Мужской"
        assert updated_user.birth_year == 1990
        assert updated_user.birth_city == "Moscow"
        assert updated_user.is_profile_complete is True

    async def test_create_natal_chart(self, test_db: AsyncDatabaseManager):
        """Тест создания натальной карты"""
        planets_data = {
            "Солнце": {"sign": "Козерог", "degree": 15.5},
            "Луна": {"sign": "Рыбы", "degree": 23.2},
        }

        chart = await test_db.create_natal_chart(
            telegram_id=12345,
            name="Test User",
            city="Moscow",
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow",
            birth_date=datetime(1990, 1, 1, 12, 0),
            birth_time_specified=True,
            has_warning=False,
            planets_data=planets_data,
        )

        assert chart is not None
        assert chart.city == "Moscow"
        assert chart.latitude == 55.7558
        assert chart.longitude == 37.6176
        assert chart.chart_type == "own"

        # Проверяем сохранение данных планет
        saved_planets = chart.get_planets_data()
        assert "Солнце" in saved_planets
        assert saved_planets["Солнце"].sign == "Козерог"
        assert saved_planets["Солнце"].degree == 15.5

    async def test_get_user_charts(self, test_db: AsyncDatabaseManager):
        """Тест получения карт пользователя"""
        # Создаем пользователя и карты
        await test_db.get_or_create_user(12345, "Test User")

        planets_data = {"Солнце": {"sign": "Козерог", "degree": 15.5}}

        chart1 = await test_db.create_natal_chart(
            telegram_id=12345,
            name="Test User",
            city="Moscow",
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow",
            birth_date=datetime(1990, 1, 1, 12, 0),
            birth_time_specified=True,
            has_warning=False,
            planets_data=planets_data,
        )

        chart2 = await test_db.create_natal_chart(
            telegram_id=12345,
            name="Test User",
            city="St. Petersburg",
            latitude=59.9311,
            longitude=30.3609,
            timezone="Europe/Moscow",
            birth_date=datetime(1985, 5, 15, 10, 30),
            birth_time_specified=True,
            has_warning=False,
            planets_data=planets_data,
            chart_type="other",
            chart_owner_name="Friend",
        )

        # Получаем все карты пользователя
        charts = await test_db.get_user_charts(12345)

        assert len(charts) == 2
        assert charts[0].id == chart2.id  # Порядок по дате создания (DESC)
        assert charts[1].id == chart1.id

    async def test_find_existing_chart(self, test_db: AsyncDatabaseManager):
        """Тест поиска существующей карты"""
        planets_data = {"Солнце": {"sign": "Козерог", "degree": 15.5}}
        birth_date = datetime(1990, 1, 1, 12, 0)

        # Создаем карту
        original_chart = await test_db.create_natal_chart(
            telegram_id=12345,
            name="Test User",
            city="Moscow",
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow",
            birth_date=birth_date,
            birth_time_specified=True,
            has_warning=False,
            planets_data=planets_data,
        )

        # Ищем существующую карту
        found_chart = await test_db.find_existing_chart(12345, "Moscow", birth_date)

        assert found_chart is not None
        assert found_chart.id == original_chart.id

        # Ищем несуществующую карту
        not_found = await test_db.find_existing_chart(12345, "London", birth_date)
        assert not_found is None

    async def test_create_and_find_prediction(self, test_db: AsyncDatabaseManager):
        """Тест создания и поиска прогнозов"""
        # Создаем пользователя и карту
        planets_data = {"Солнце": {"sign": "Козерог", "degree": 15.5}}
        chart = await test_db.create_natal_chart(
            telegram_id=12345,
            name="Test User",
            city="Moscow",
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow",
            birth_date=datetime(1990, 1, 1, 12, 0),
            birth_time_specified=True,
            has_warning=False,
            planets_data=planets_data,
        )

        # Создаем прогноз
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)

        prediction = await test_db.create_prediction(
            telegram_id=12345,
            chart_id=chart.id,
            prediction_type="сегодня",
            valid_from=now,
            valid_until=tomorrow,
            content="Тестовый прогноз",
            generation_time=1.5,
        )

        assert prediction is not None
        assert prediction.content == "Тестовый прогноз"
        assert prediction.generation_time == 1.5

        # Ищем действующий прогноз
        found_prediction = await test_db.find_valid_prediction(
            12345, chart.id, "сегодня"
        )

        assert found_prediction is not None
        assert found_prediction.id == prediction.id

        # Ищем несуществующий тип прогноза
        not_found = await test_db.find_valid_prediction(12345, chart.id, "неделя")
        assert not_found is None

    async def test_subscription_management(self, test_db: AsyncDatabaseManager):
        """Тест управления подписками"""
        # Создаем подписку
        subscription = await test_db.get_or_create_subscription(12345)

        assert subscription is not None
        assert subscription.subscription_type == SubscriptionType.FREE
        assert subscription.is_active is True

        # Получаем существующую подписку
        subscription2 = await test_db.get_or_create_subscription(12345)

        assert subscription2.id == subscription.id

    async def test_get_statistics(self, test_db: AsyncDatabaseManager):
        """Тест получения статистики"""
        # Создаем тестовые данные
        await test_db.get_or_create_user(12345, "User 1")
        await test_db.get_or_create_user(67890, "User 2")

        planets_data = {"Солнце": {"sign": "Козерог", "degree": 15.5}}
        await test_db.create_natal_chart(
            telegram_id=12345,
            name="User 1",
            city="Moscow",
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow",
            birth_date=datetime(1990, 1, 1, 12, 0),
            birth_time_specified=True,
            has_warning=False,
            planets_data=planets_data,
        )

        # Получаем статистику
        stats = await test_db.get_app_statistics()

        assert stats["total_users"] == 2
        assert stats["total_charts"] == 1
        assert stats["new_users_today"] == 2  # Оба созданы сегодня
        assert stats["active_premium"] == 0  # Нет премиум подписок

    async def test_notifications_setting(self, test_db: AsyncDatabaseManager):
        """Тест настройки уведомлений"""
        # Создаем пользователя
        user, _ = await test_db.get_or_create_user(12345, "Test User")
        assert user.notifications_enabled is True  # По умолчанию включены

        # Отключаем уведомления
        success = await test_db.set_notifications(12345, False)
        assert success is True

        # Проверяем что настройка сохранилась
        updated_user = await test_db.get_user_profile(12345)
        assert updated_user.notifications_enabled is False

    async def test_cleanup_expired_predictions(self, test_db: AsyncDatabaseManager):
        """Тест очистки устаревших прогнозов"""
        # Создаем пользователя и карту
        planets_data = {"Солнце": {"sign": "Козерог", "degree": 15.5}}
        chart = await test_db.create_natal_chart(
            telegram_id=12345,
            name="Test User",
            city="Moscow",
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow",
            birth_date=datetime(1990, 1, 1, 12, 0),
            birth_time_specified=True,
            has_warning=False,
            planets_data=planets_data,
        )

        # Создаем устаревший прогноз
        yesterday = datetime.utcnow() - timedelta(days=1)
        day_before = datetime.utcnow() - timedelta(days=2)

        await test_db.create_prediction(
            telegram_id=12345,
            chart_id=chart.id,
            prediction_type="вчера",
            valid_from=day_before,
            valid_until=yesterday,  # Уже истек
            content="Устаревший прогноз",
        )

        # Создаем актуальный прогноз
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)

        await test_db.create_prediction(
            telegram_id=12345,
            chart_id=chart.id,
            prediction_type="сегодня",
            valid_from=now,
            valid_until=tomorrow,
            content="Актуальный прогноз",
        )

        # Очищаем устаревшие прогнозы
        deleted_count = await test_db.cleanup_expired_predictions()

        assert deleted_count == 1  # Один прогноз должен быть удален

        # Проверяем что актуальный прогноз остался
        remaining = await test_db.find_valid_prediction(12345, chart.id, "сегодня")
        assert remaining is not None
        assert remaining.content == "Актуальный прогноз"


@pytest.mark.asyncio
@pytest.mark.database
class TestAsyncDatabasePerformance:
    """Тесты производительности асинхронной базы данных"""

    async def test_concurrent_user_creation(self, test_db: AsyncDatabaseManager):
        """Тест одновременного создания пользователей"""
        import asyncio

        async def create_user(user_id: int):
            user, created = await test_db.get_or_create_user(user_id, f"User {user_id}")
            return user, created

        # Создаем 10 пользователей одновременно
        tasks = [create_user(i) for i in range(1000, 1010)]
        results = await asyncio.gather(*tasks)

        # Проверяем что все пользователи созданы
        assert len(results) == 10
        for user, created in results:
            assert created is True
            assert user.telegram_id >= 1000 and user.telegram_id < 1010

        # Проверяем общее количество
        total_users = await test_db.get_total_users_count()
        assert total_users == 10
