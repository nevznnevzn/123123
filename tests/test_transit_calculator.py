import zoneinfo
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from models import Location
from services.transit_calculator import TransitCalculator


class TestTransitCalculator:
    """Тесты для калькулятора транзитов"""

    def test_init_creates_transit_planets(self):
        """Тест: инициализация создает словарь планет для транзитов"""
        calculator = TransitCalculator()

        assert calculator.transit_planets is not None
        assert len(calculator.transit_planets) == 10  # 10 основных планет
        assert "Солнце" in calculator.transit_planets.values()
        assert "Плутон" in calculator.transit_planets.values()

    @patch("swisseph.calc_ut")
    @patch("swisseph.julday")
    def test_calculate_natal_planets_success(self, mock_julday, mock_calc_ut):
        """Тест: успешный расчет натальных планет"""
        # Настройка моков
        mock_julday.return_value = 2460000.0
        mock_calc_ut.return_value = ([120.5, 0, 0], 0)  # [долгота, широта, расстояние]

        calculator = TransitCalculator()
        location = Location(
            city="Москва", lat=55.7558, lng=37.6176, timezone="Europe/Moscow"
        )
        birth_dt = datetime(
            1990, 6, 15, 12, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Moscow")
        )

        planets = calculator._calculate_natal_planets(birth_dt, location)

        assert len(planets) == 10  # Все 10 планет должны быть рассчитаны
        for planet_name in calculator.transit_planets.values():
            assert planet_name in planets
            assert planets[planet_name] == 120.5

    @patch("swisseph.calc_ut")
    @patch("swisseph.julday")
    def test_calculate_current_planets_success(self, mock_julday, mock_calc_ut):
        """Тест: успешный расчет текущих планет"""
        # Настройка моков - теперь возвращаем расширенные данные с скоростью
        mock_julday.return_value = 2460000.0
        mock_calc_ut.return_value = ([180.0, 0, 0, 1.0], 0)  # добавляем скорость

        calculator = TransitCalculator()
        location = Location(
            city="Москва", lat=55.7558, lng=37.6176, timezone="Europe/Moscow"
        )
        current_dt = datetime.now(zoneinfo.ZoneInfo("Europe/Moscow"))

        planets = calculator._calculate_current_planets(current_dt, location)

        assert len(planets) == 10
        for planet_name in calculator.transit_planets.values():
            assert planet_name in planets
            # Теперь возвращается кортеж (позиция, ретроградность)
            position, is_retrograde = planets[planet_name]
            assert position == 180.0
            assert isinstance(is_retrograde, bool)

    def test_analyze_transits_improved_conjunction(self):
        """Тест: улучшенный анализ транзитов - соединение"""
        calculator = TransitCalculator()

        # Тестовые данные: натальная планета в 120°, транзитная в 120.5° (разница 0.5° - соединение)
        natal_planets = {"Солнце": 120.0}
        current_planets = {"Солнце": (120.5, False)}  # (позиция, ретроградность)
        current_dt = datetime.now()

        transits = calculator._analyze_transits_improved(
            natal_planets, current_planets, current_dt
        )

        assert len(transits) >= 1
        transit_desc = transits[0]
        assert "соединение" in transit_desc
        assert "Солнце" in transit_desc
        assert "натальный" in transit_desc

    def test_analyze_transits_improved_opposition(self):
        """Тест: улучшенный анализ транзитов - оппозиция"""
        calculator = TransitCalculator()

        # Тестовые данные: натальная планета в 0°, транзитная в 180° (оппозиция)
        natal_planets = {"Солнце": 0.0}
        current_planets = {"Луна": (180.0, False)}
        current_dt = datetime.now()

        transits = calculator._analyze_transits_improved(
            natal_planets, current_planets, current_dt
        )

        assert len(transits) >= 1
        transit_desc = transits[0]
        assert "оппозиция" in transit_desc
        assert "Луна" in transit_desc
        assert "натальный Солнце" in transit_desc

    def test_analyze_transits_improved_square(self):
        """Тест: улучшенный анализ транзитов - квадрат"""
        calculator = TransitCalculator()

        # Тестовые данные: натальная планета в 0°, транзитная в 90° (квадрат)
        natal_planets = {"Солнце": 0.0}
        current_planets = {"Марс": (90.0, False)}
        current_dt = datetime.now()

        transits = calculator._analyze_transits_improved(
            natal_planets, current_planets, current_dt
        )

        assert len(transits) >= 1
        transit_desc = transits[0]
        assert "квадрат" in transit_desc

    def test_analyze_transits_improved_trine(self):
        """Тест: улучшенный анализ транзитов - трин"""
        calculator = TransitCalculator()

        # Тестовые данные: натальная планета в 0°, транзитная в 120° (трин)
        natal_planets = {"Солнце": 0.0}
        current_planets = {"Юпитер": (120.0, False)}
        current_dt = datetime.now()

        transits = calculator._analyze_transits_improved(
            natal_planets, current_planets, current_dt
        )

        assert len(transits) >= 1
        transit_desc = transits[0]
        assert "трин" in transit_desc

    def test_analyze_transits_improved_no_aspects(self):
        """Тест: улучшенный анализ транзитов - нет аспектов"""
        calculator = TransitCalculator()

        # Тестовые данные: большая разница в градусах, нет значимых аспектов
        natal_planets = {"Солнце": 0.0}
        current_planets = {
            "Луна": (45.0, False)
        }  # 45° - не входит в орбы основных аспектов
        current_dt = datetime.now()

        transits = calculator._analyze_transits_improved(
            natal_planets, current_planets, current_dt
        )

        assert len(transits) == 0

    def test_analyze_transits_retrograde_marking(self):
        """Тест: отметка ретроградности в транзитах"""
        calculator = TransitCalculator()

        # Тестовые данные с ретроградной планетой
        natal_planets = {"Солнце": 120.0}
        current_planets = {"Меркурий": (120.5, True)}  # Ретроградный Меркурий
        current_dt = datetime.now()

        transits = calculator._analyze_transits_improved(
            natal_planets, current_planets, current_dt
        )

        assert len(transits) >= 1
        transit_desc = transits[0]
        assert "(R)" in transit_desc  # Должна быть отметка ретроградности

    @patch.object(TransitCalculator, "get_current_transits")
    def test_get_transit_summary_with_transits(self, mock_get_transits):
        """Тест: получение краткого описания с транзитами"""
        mock_transits = [
            "Солнце ☌ натальный Солнце (соединение, точный, орб 0.2°)",
            "Луна ☍ натальный Марс (оппозиция, тесный, орб 1.1°)",
        ]
        mock_get_transits.return_value = mock_transits

        calculator = TransitCalculator()
        location = Location(
            city="Москва", lat=55.7558, lng=37.6176, timezone="Europe/Moscow"
        )
        birth_dt = datetime(
            1990, 6, 15, 12, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Moscow")
        )

        summary = calculator.get_transit_summary(birth_dt, location)

        assert "🌟 Текущие астрологические транзиты:" in summary
        assert "1. Солнце ☌ натальный Солнце" in summary
        assert "2. Луна ☍ натальный Марс" in summary

    @patch.object(TransitCalculator, "get_current_transits")
    def test_get_transit_summary_no_transits(self, mock_get_transits):
        """Тест: получение краткого описания без транзитов"""
        mock_get_transits.return_value = []

        calculator = TransitCalculator()
        location = Location(
            city="Москва", lat=55.7558, lng=37.6176, timezone="Europe/Moscow"
        )
        birth_dt = datetime(
            1990, 6, 15, 12, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Moscow")
        )

        summary = calculator.get_transit_summary(birth_dt, location)

        assert summary == "В данный момент нет активных значимых транзитов."

    @patch("swisseph.calc_ut")
    def test_calculate_natal_planets_swisseph_error(self, mock_calc_ut):
        """Тест: обработка ошибки Swiss Ephemeris"""
        mock_calc_ut.side_effect = Exception("Swiss Ephemeris error")

        calculator = TransitCalculator()
        location = Location(
            city="Москва", lat=55.7558, lng=37.6176, timezone="Europe/Moscow"
        )
        birth_dt = datetime(
            1990, 6, 15, 12, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Moscow")
        )

        planets = calculator._calculate_natal_planets(birth_dt, location)

        assert planets == {}

    def test_normalize_angle(self):
        """Тест: нормализация углов"""
        calculator = TransitCalculator()

        assert calculator._normalize_angle(370) == 10
        assert calculator._normalize_angle(-10) == 350
        assert calculator._normalize_angle(180) == 180
        assert calculator._normalize_angle(0) == 0

    def test_calculate_angular_distance(self):
        """Тест: расчет углового расстояния"""
        calculator = TransitCalculator()

        # Обычные случаи
        assert calculator._calculate_angular_distance(0, 90) == 90
        assert calculator._calculate_angular_distance(90, 0) == 90
        assert calculator._calculate_angular_distance(0, 180) == 180

        # Через границу 360°
        assert calculator._calculate_angular_distance(10, 350) == 20
        assert calculator._calculate_angular_distance(350, 10) == 20


if __name__ == "__main__":
    pytest.main([__file__])
