from datetime import datetime

import pytest

from config import Config
from models import Location
from services.astro_calculations import (
    AstroCalculator,
    AstroService,
    validate_datetime,
    validate_location,
)


@pytest.fixture
def calculator():
    """Фикстура для создания экземпляра AstroCalculator."""
    return AstroCalculator()


@pytest.fixture
def astro_service():
    """Фикстура для создания экземпляра AstroService."""
    return AstroService()


@pytest.mark.asyncio
async def test_calculate_planets_is_deterministic(calculator: AstroCalculator):
    """
    Тест проверяет, что для одной и той же даты рождения
    результат вычислений всегда одинаковый.
    """
    birth_date = datetime(1990, 5, 15)
    location = Location(city="Test City", lat=0, lng=0, timezone="UTC")
    
    # Вызываем функцию дважды с одинаковыми данными
    planets1 = await calculator.calculate_planets(birth_date, location)
    planets2 = await calculator.calculate_planets(birth_date, location)
    
    # Сравниваем результаты
    assert planets1 == planets2


@pytest.mark.asyncio
async def test_planets_basic_validation(calculator: AstroCalculator):
    """
    Тест проверяет базовую валидность астрологических расчетов.
    Проверяем, что все планеты рассчитаны корректно и находятся в допустимых пределах.
    """
    birth_date = datetime(1990, 5, 15, 12, 0)
    location = Location(city="Test City", lat=0, lng=0, timezone="UTC")

    planets = await calculator.calculate_planets(birth_date, location)

    # Проверяем, что все основные планеты присутствуют
    expected_planets = [
        "Солнце",
        "Луна",
        "Меркурий",
        "Венера",
        "Марс",
        "Юпитер",
        "Сатурн",
        "Уран",
        "Нептун",
        "Плутон",
    ]

    for planet in expected_planets:
        assert planet in planets, f"Планета {planet} отсутствует в результатах"

        # Проверяем, что знак зодиака корректный
        assert (
            planets[planet].sign in Config.ZODIAC_SIGNS
        ), f"Неверный знак для {planet}"

        # Проверяем, что градус находится в допустимых пределах (0-30)
        assert (
            0 <= planets[planet].degree < 30
        ), f"Неверный градус для {planet}: {planets[planet].degree}"


def test_sun_position_verification(calculator: AstroCalculator):
    """
    Тест проверяет корректность позиции Солнца для известной даты.
    15 мая 1990 - Солнце должно быть в знаке Тельца (примерно 24-25°).
    """
    birth_date = datetime(1990, 5, 15, 12, 0)
    location = Location(city="Test City", lat=0, lng=0, timezone="UTC")

    planets = calculator.calculate_planets(birth_date, location)

    assert "Солнце" in planets
    # В середине мая Солнце находится в Тельце
    assert planets["Солнце"].sign == "Телец"
    # Примерно в районе 24-25 градусов Тельца
    assert 20 <= planets["Солнце"].degree <= 30


def test_mercury_venus_near_sun(calculator: AstroCalculator):
    """
    Тест проверяет, что Меркурий и Венера находятся относительно близко к Солнцу.
    Это базовая астрономическая проверка.
    """
    birth_date = datetime(1990, 5, 15, 12, 0)
    location = Location(city="Test City", lat=0, lng=0, timezone="UTC")
    
    planets = calculator.calculate_planets(birth_date, location)
    
    # Получаем абсолютные позиции
    sun_abs = (
        Config.ZODIAC_SIGNS.index(planets["Солнце"].sign) * 30
        + planets["Солнце"].degree
    )
    mercury_abs = (
        Config.ZODIAC_SIGNS.index(planets["Меркурий"].sign) * 30
        + planets["Меркурий"].degree
    )
    venus_abs = (
        Config.ZODIAC_SIGNS.index(planets["Венера"].sign) * 30
        + planets["Венера"].degree
    )

    # Меркурий не должен быть дальше 28° от Солнца
    mercury_distance = min(abs(sun_abs - mercury_abs), 360 - abs(sun_abs - mercury_abs))
    assert (
        mercury_distance <= 28
    ), f"Меркурий слишком далеко от Солнца: {mercury_distance}°"

    # Венера не должна быть дальше 48° от Солнца
    venus_distance = min(abs(sun_abs - venus_abs), 360 - abs(sun_abs - venus_abs))
    assert venus_distance <= 48, f"Венера слишком далеко от Солнца: {venus_distance}°"


def test_validate_location():
    """Тест валидации местоположения"""
    # Корректное местоположение
    valid_location = Location(
        city="Moscow", lat=55.7558, lng=37.6176, timezone="Europe/Moscow"
    )
    assert validate_location(valid_location) == True

    # Неверная широта
    invalid_lat = Location(city="Invalid", lat=100, lng=0, timezone="UTC")
    assert validate_location(invalid_lat) == False

    # Неверная долгота
    invalid_lng = Location(city="Invalid", lat=0, lng=200, timezone="UTC")
    assert validate_location(invalid_lng) == False


def test_validate_datetime():
    """Тест валидации даты и времени"""
    # Корректная дата
    valid_date = datetime(1990, 5, 15, 12, 0)
    assert validate_datetime(valid_date) == True

    # Некорректный тип
    assert validate_datetime("not a date") == False

    # Дата вне рекомендуемого диапазона (должна выдать предупреждение, но вернуть True)
    old_date = datetime(1700, 1, 1)
    assert validate_datetime(old_date) == True


def test_calculation_quality_validation(astro_service: AstroService):
    """Тест валидации качества расчетов"""
    birth_date = datetime(1990, 5, 15, 12, 0)
    location = Location(city="Test City", lat=0, lng=0, timezone="UTC")

    planets = astro_service.calculate_natal_chart(birth_date, location)
    is_valid, message = astro_service.validate_calculation_quality(planets)

    assert is_valid == True
    assert "отличное" in message


def test_error_handling_invalid_input(calculator: AstroCalculator):
    """Тест обработки неверных входных данных"""
    # Неверная дата
    invalid_date = "not a date"
    location = Location(city="Test", lat=0, lng=0, timezone="UTC")

    planets = calculator.calculate_planets(invalid_date, location)
    assert planets == {}

    # Неверное местоположение
    valid_date = datetime(1990, 5, 15)
    invalid_location = None

    planets = calculator.calculate_planets(valid_date, invalid_location)
    assert planets == {}


def test_timezone_handling(calculator: AstroCalculator):
    """Тест корректной обработки временных зон"""
    # Дата без временной зоны
    birth_date = datetime(1990, 5, 15, 12, 0)
    location = Location(
        city="Moscow", lat=55.7558, lng=37.6176, timezone="Europe/Moscow"
    )

    planets = calculator.calculate_planets(birth_date, location)

    # Проверяем, что расчет прошел успешно
    assert len(planets) > 0
    assert "Солнце" in planets


def test_extreme_coordinates(calculator: AstroCalculator):
    """Тест расчетов для экстремальных координат"""
    birth_date = datetime(1990, 6, 21, 12, 0)  # Летнее солнцестояние

    # Северный полюс
    arctic_location = Location(city="North Pole", lat=89.9, lng=0, timezone="UTC")
    planets_arctic = calculator.calculate_planets(birth_date, arctic_location)

    # Южный полюс
    antarctic_location = Location(city="South Pole", lat=-89.9, lng=0, timezone="UTC")
    planets_antarctic = calculator.calculate_planets(birth_date, antarctic_location)

    # Планеты должны быть рассчитаны в обоих случаях
    assert len(planets_arctic) > 0
    assert len(planets_antarctic) > 0


def test_leap_year_calculation(calculator: AstroCalculator):
    """Тест расчетов для високосного года"""
    # 29 февраля 2000 года (високосный год)
    birth_date = datetime(2000, 2, 29, 12, 0)
    location = Location(city="Test", lat=0, lng=0, timezone="UTC")

    planets = calculator.calculate_planets(birth_date, location)

    # Проверяем успешность расчета
    assert len(planets) > 0
    assert "Солнце" in planets
    assert planets["Солнце"].sign == "Рыбы"  # Конец февраля - Рыбы


def test_historical_date_calculation(calculator: AstroCalculator):
    """Тест расчетов для исторической даты"""
    # 1 января 1900 года
    birth_date = datetime(1900, 1, 1, 12, 0)
    location = Location(city="Greenwich", lat=51.4769, lng=0, timezone="UTC")

    planets = calculator.calculate_planets(birth_date, location)

    # Проверяем успешность расчета для исторической даты
    assert len(planets) > 0
    assert "Солнце" in planets
    assert planets["Солнце"].sign == "Козерог"  # 1 января - Козерог


def test_future_date_calculation(calculator: AstroCalculator):
    """Тест расчетов для будущей даты"""
    # 1 января 2100 года
    birth_date = datetime(2100, 1, 1, 12, 0)
    location = Location(city="Test", lat=0, lng=0, timezone="UTC")

    planets = calculator.calculate_planets(birth_date, location)

    # Проверяем успешность расчета для будущей даты
    assert len(planets) > 0
    assert "Солнце" in planets


def test_planet_description_service(astro_service: AstroService):
    """Тест получения описаний планет"""
    # Корректные данные
    description = astro_service.get_planet_description("Солнце", "Овен")
    assert isinstance(description, str)
    assert len(description) > 0

    # Неверные данные
    invalid_description = astro_service.get_planet_description("", "")
    assert "недоступно" in invalid_description.lower()


def test_consistency_across_multiple_calculations(calculator: AstroCalculator):
    """Тест консистентности между множественными расчетами"""
    birth_date = datetime(1985, 3, 15, 14, 30)
    location = Location(city="Paris", lat=48.8566, lng=2.3522, timezone="Europe/Paris")

    # Выполняем расчет несколько раз
    results = []
    for _ in range(3):
        planets = calculator.calculate_planets(birth_date, location)
        results.append(planets)

    # Все результаты должны быть одинаковыми
    for i in range(1, len(results)):
        assert results[0] == results[i], f"Результат {i} отличается от первого"
