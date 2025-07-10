import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from database import NatalChart, User, db_manager
from services.motivation_service import MotivationService


class TestMotivationService:

    @pytest.fixture
    def mock_ai_service(self):
        ai_service = Mock()
        ai_service.get_chat_completion = AsyncMock(
            return_value="Великолепная мотивация на день!"
        )
        return ai_service

    @pytest.fixture
    def motivation_service(self, mock_ai_service):
        return MotivationService(mock_ai_service)

    @pytest.fixture
    def test_user(self):
        return User(telegram_id=123456789, name="Тест Пользователь")

    @pytest.mark.asyncio
    async def test_generate_motivation_without_charts(
        self, motivation_service, test_user, mock_ai_service
    ):
        """Тест генерации мотивации когда у пользователя нет натальных карт"""
        with patch("services.motivation_service.db_manager") as mock_db:
            mock_db.get_user_charts.return_value = []
            with patch.object(
                motivation_service.subscription_service,
                "is_user_premium",
                return_value=False,
            ):
                result = await motivation_service.generate_motivation(test_user)

                assert result is not None
                assert "Великолепная мотивация на день!" in result
                assert "Premium подписку" in result  # Проверяем призыв к подписке
                mock_ai_service.get_chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_motivation_with_premium(
        self, motivation_service, test_user, mock_ai_service
    ):
        """Тест генерации мотивации для премиум пользователя"""
        # Создаем тестовую натальную карту
        mock_chart = Mock(spec=NatalChart)
        mock_chart.birth_date = "1990-01-01"
        mock_chart.get_planets_data.return_value = {
            "Sun": Mock(sign="Козерог", degree=10.5),
            "Moon": Mock(sign="Рыбы", degree=23.2),
            "Mercury": Mock(sign="Козерог", degree=15.8),
        }

        with patch("services.motivation_service.db_manager") as mock_db:
            mock_db.get_user_charts.return_value = [mock_chart]
            with patch.object(
                motivation_service.subscription_service,
                "is_user_premium",
                return_value=True,
            ):
                with patch.object(
                    motivation_service.subscription_service,
                    "filter_planets_for_user",
                    return_value=mock_chart.get_planets_data(),
                ):
                    result = await motivation_service.generate_motivation(test_user)

                    assert result is not None
                    assert "Premium подписку" not in result  # Для премиум нет призыва
                    # Проверяем что был вызван с астрологическим промптом
                    call_args = mock_ai_service.get_chat_completion.call_args
                    assert "Натальная карта:" in call_args[1]["prompt"]

    @pytest.mark.asyncio
    async def test_generate_motivation_free_user_with_chart(
        self, motivation_service, test_user, mock_ai_service
    ):
        """Тест генерации мотивации для бесплатного пользователя с натальной картой"""
        mock_chart = Mock(spec=NatalChart)
        mock_chart.birth_date = "1990-01-01"
        mock_chart.get_planets_data.return_value = {
            "Sun": Mock(sign="Козерог", degree=10.5),
            "Moon": Mock(sign="Рыбы", degree=23.2),
        }

        # Фильтрованные планеты для бесплатного пользователя
        filtered_planets = {"Sun": Mock(sign="Козерог", degree=10.5)}

        with patch("services.motivation_service.db_manager") as mock_db:
            mock_db.get_user_charts.return_value = [mock_chart]
            with patch.object(
                motivation_service.subscription_service,
                "is_user_premium",
                return_value=False,
            ):
                with patch.object(
                    motivation_service.subscription_service,
                    "filter_planets_for_user",
                    return_value=filtered_planets,
                ):
                    result = await motivation_service.generate_motivation(test_user)

                    assert result is not None
                    assert (
                        "Premium подписку" in result
                    )  # Призыв к подписке для бесплатного
                    # Проверяем что промпт содержит только одну планету
                    call_args = mock_ai_service.get_chat_completion.call_args
                    prompt = call_args[1]["prompt"]
                    assert "Козерог" in prompt
                    assert "Рыбы" not in prompt  # Луна должна быть отфильтрована

    @pytest.mark.asyncio
    async def test_generate_motivation_with_chart_no_planets(
        self, motivation_service, test_user, mock_ai_service
    ):
        """Тест когда натальная карта есть, но планеты не найдены"""
        mock_chart = Mock(spec=NatalChart)
        mock_chart.get_planets_data.return_value = {}

        with patch("services.motivation_service.db_manager") as mock_db:
            mock_db.get_user_charts.return_value = [mock_chart]
            with patch.object(
                motivation_service.subscription_service,
                "is_user_premium",
                return_value=False,
            ):
                result = await motivation_service.generate_motivation(test_user)

                assert result is not None
                assert "Premium подписку" in result

    @pytest.mark.asyncio
    async def test_generate_motivation_ai_error(self, motivation_service, test_user):
        """Тест обработки ошибки AI сервиса"""
        mock_ai_service = Mock()
        mock_ai_service.get_chat_completion = AsyncMock(
            side_effect=Exception("AI service error")
        )
        motivation_service.ai_service = mock_ai_service

        with patch("services.motivation_service.db_manager") as mock_db:
            mock_db.get_user_charts.return_value = []
            with patch.object(
                motivation_service.subscription_service,
                "is_user_premium",
                return_value=False,
            ):
                result = await motivation_service.generate_motivation(test_user)

                assert result is None  # При ошибке в обоих методах возвращается None

    @pytest.mark.asyncio
    async def test_explicit_subscription_parameter(
        self, motivation_service, test_user, mock_ai_service
    ):
        """Тест что явный параметр подписки имеет приоритет"""
        with patch("services.motivation_service.db_manager") as mock_db:
            mock_db.get_user_charts.return_value = []
            # is_user_premium возвращает False, но мы передаем True явно
            with patch.object(
                motivation_service.subscription_service,
                "is_user_premium",
                return_value=False,
            ):
                result = await motivation_service.generate_motivation(
                    test_user, is_subscribed=True
                )

                assert result is not None
                assert (
                    "Premium подписку" not in result
                )  # Не должно быть призыва для премиум

    def test_create_astro_prompt_premium(self, motivation_service):
        """Тест создания астрологического промпта для премиум пользователя"""
        planets = {
            "Sun": Mock(sign="Лев", degree=15.5),
            "Moon": Mock(sign="Скорпион", degree=22.3),
        }

        prompt = motivation_service._create_astro_prompt(
            user_name="Анна",
            planets=planets,
            birth_date="1990-08-15",
            is_subscribed=True,
        )

        assert "Анна" in prompt
        assert "Лев" in prompt
        assert "Скорпион" in prompt
        assert "детальную астрологическую мотивацию" in prompt
        assert "3-4 абзаца" in prompt

    def test_create_astro_prompt_free(self, motivation_service):
        """Тест создания астрологического промпта для бесплатного пользователя"""
        planets = {"Sun": Mock(sign="Дева", degree=8.2)}

        prompt = motivation_service._create_astro_prompt(
            user_name="Иван",
            planets=planets,
            birth_date="1985-09-01",
            is_subscribed=False,
        )

        assert "Иван" in prompt
        assert "Дева" in prompt
        assert "краткую астрологическую мотивацию" in prompt
        assert "2-3 предложения" in prompt
