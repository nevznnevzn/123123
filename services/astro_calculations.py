import logging
import threading
import zoneinfo
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import swisseph as swe

from config import Config
from models import Location, PlanetPosition
from services.zodiac_data_loader import (  # Импортируем экземпляр загрузчика
    zodiac_data_loader,
)

logger = logging.getLogger(__name__)

# Глобальная блокировка для Swiss Ephemeris (не потокобезопасен)
swe_lock = threading.Lock()

# Устанавливаем путь к файлам эфемерид
swe.set_ephe_path(".")


def get_zodiac_sign(longitude: float) -> tuple[str, float]:
    """Определяет знак зодиака и градус в нем по долготе"""
    # Валидация входных данных
    if not isinstance(longitude, (int, float)):
        logger.error(f"Неверный тип долготы: {type(longitude)}")
        return Config.ZODIAC_SIGNS[0], 0.0

    # Нормализация долготы к диапазону 0-360
    while longitude < 0:
        longitude += 360
    while longitude >= 360:
        longitude -= 360

    sign_index = int(longitude / 30)
    degree = longitude % 30

    # Дополнительная проверка
    if sign_index < 0 or sign_index >= 12:
        logger.warning(f"Аномальный индекс знака: {sign_index} для долготы {longitude}")
        sign_index = 0

    sign = Config.ZODIAC_SIGNS[sign_index]
    return sign, degree


def validate_location(location: Location) -> bool:
    """Валидирует данные местоположения"""
    if not location:
        logger.error("Местоположение не указано")
        return False

    if not hasattr(location, "lat") or not hasattr(location, "lng"):
        logger.error("Некорректная структура местоположения")
        return False

    # Проверка широты
    if not isinstance(location.lat, (int, float)) or not (-90 <= location.lat <= 90):
        logger.error(f"Неверная широта: {location.lat}")
        return False

    # Проверка долготы
    if not isinstance(location.lng, (int, float)) or not (-180 <= location.lng <= 180):
        logger.error(f"Неверная долгота: {location.lng}")
        return False

    # Проверка временной зоны
    if not hasattr(location, "timezone") or not location.timezone:
        logger.warning("Временная зона не указана, будет использована UTC")
        location.timezone = "UTC"

    return True


def validate_datetime(dt: datetime) -> bool:
    """Валидирует дату и время"""
    if not isinstance(dt, datetime):
        logger.error(f"Неверный тип даты: {type(dt)}")
        return False

    # Проверка разумных пределов даты (1800-2200)
    if dt.year < 1800 or dt.year > 2200:
        logger.warning(f"Дата вне рекомендуемого диапазона: {dt.year}")

    return True


class AstroCalculator:
    """Астрологический калькулятор для основных вычислений"""

    PLANETS_TO_CALCULATE = {
        "Солнце": swe.SUN,
        "Луна": swe.MOON,
        "Меркурий": swe.MERCURY,
        "Венера": swe.VENUS,
        "Марс": swe.MARS,
        "Юпитер": swe.JUPITER,
        "Сатурн": swe.SATURN,
        "Уран": swe.URANUS,
        "Нептун": swe.NEPTUNE,
        "Плутон": swe.PLUTO,
    }

    def __init__(self):
        # Инициализируем сервис геокодирования
        from .geocoding_service import GeocodingService

        self.geocoding_service = GeocodingService()
        self._validate_ephemeris_files()

    def _validate_ephemeris_files(self) -> None:
        """Проверяет наличие и корректность файлов эфемерид"""
        try:
            import os

            ephe_files = [f for f in os.listdir(".") if f.endswith(".bsp")]
            if not ephe_files:
                logger.warning(
                    "Файлы эфемерид Swiss Ephemeris не найдены в текущей директории"
                )
            else:
                logger.info(f"Найдены файлы эфемерид: {ephe_files}")

            # Тестовый расчет для проверки работы Swiss Ephemeris
            test_jd = swe.julday(2024, 1, 1, 12.0)
            test_result = swe.calc_ut(test_jd, swe.SUN)
            if test_result and len(test_result[0]) > 0:
                logger.info("Swiss Ephemeris работает корректно")
            else:
                logger.error("Проблема с Swiss Ephemeris")

        except Exception as e:
            logger.error(f"Ошибка проверки эфемерид: {e}")

    def get_location(self, city_name: str) -> Optional[Location]:
        """Получить координаты города через геокодирование"""
        if not city_name or not isinstance(city_name, str):
            logger.error("Неверное название города")
            return None

        try:
            location = self.geocoding_service.get_location(city_name)
            if location and validate_location(location):
                logger.info(
                    f"Получены координаты для {city_name}: {location.lat}, {location.lng}"
                )
                return location
            else:
                logger.warning(
                    f"Не удалось получить корректные координаты для {city_name}"
                )
                return None
        except Exception as e:
            logger.error(f"Ошибка геокодирования для {city_name}: {e}")
            return None

    def _validate_swe_result(self, result: Any, planet_name: str) -> bool:
        """Валидирует результат от Swiss Ephemeris"""
        if not result:
            logger.warning(f"Пустой результат для {planet_name}")
            return False

        if not hasattr(result, "__len__") or len(result) < 1:
            logger.warning(f"Некорректная структура результата для {planet_name}")
            return False

        coordinates = result[0]
        if not hasattr(coordinates, "__len__") or len(coordinates) < 1:
            logger.warning(f"Отсутствуют координаты для {planet_name}")
            return False

        longitude = coordinates[0]
        if not isinstance(longitude, (int, float)):
            logger.warning(f"Неверный тип долготы для {planet_name}: {type(longitude)}")
            return False

        # Проверка на разумные пределы
        if not (0 <= longitude < 360):
            logger.warning(f"Долгота вне диапазона для {planet_name}: {longitude}")
            # Нормализуем
            while longitude < 0:
                longitude += 360
            while longitude >= 360:
                longitude -= 360
            result[0][0] = longitude

        return True

    async def calculate_planets(
        self, birth_date: datetime, location: Location
    ) -> Dict[str, PlanetPosition]:
        """Вычислить позиции планет с использованием Swiss Ephemeris асинхронно"""
        # Валидация входных данных
        if not validate_datetime(birth_date):
            logger.error("Неверная дата рождения")
            return {}

        if not validate_location(location):
            logger.error("Неверные данные местоположения")
            return {}

        logger.info(f"Начало расчета планет для {birth_date} в {location.city}")
        
        try:
            # Убеждаемся, что дата и время имеют часовой пояс
            if birth_date.tzinfo is None:
                try:
                    tz = zoneinfo.ZoneInfo(location.timezone)
                    birth_date = birth_date.replace(tzinfo=tz)
                    logger.info(f"Добавлена временная зона: {location.timezone}")
                except Exception as e:
                    logger.warning(
                        f"Ошибка с временной зоной {location.timezone}, используем UTC: {e}"
                    )
                    birth_date = birth_date.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

            # Переводим время в UTC для расчетов
            utc_dt = birth_date.astimezone(zoneinfo.ZoneInfo("UTC"))
            logger.debug(f"UTC время для расчетов: {utc_dt}")

            # Рассчитываем юлианскую дату
            julian_day = swe.julday(
                utc_dt.year,
                utc_dt.month,
                utc_dt.day,
                utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
            )
            logger.debug(f"Юлианская дата: {julian_day}")

            # Выполняем расчеты Swiss Ephemeris в отдельном потоке
            planets = await self._calculate_planets_async(julian_day)

            # Проверяем качество результатов
            success_rate = len(planets) / len(self.PLANETS_TO_CALCULATE) * 100
            logger.info(
                f"Успешно рассчитано {len(planets)}/{len(self.PLANETS_TO_CALCULATE)} планет ({success_rate:.1f}%)"
            )

            # Дополнительная валидация результатов
            self._validate_planet_positions(planets)

            return planets

        except Exception as e:
            logger.error(f"Критическая ошибка при расчете планет: {e}")
            return {}

    async def _calculate_planets_async(self, julian_day: float) -> Dict[str, PlanetPosition]:
        """Асинхронно выполняет расчеты планет через executor"""
        import asyncio
        
        def sync_calculate_planets():
            """Синхронная функция расчета планет для выполнения в executor"""
            planets = {}
            calculation_errors = []
            
            with swe_lock:
                # Рассчитываем позиции для каждой планеты
                for planet_name, planet_id in self.PLANETS_TO_CALCULATE.items():
                    try:
                        # swe.calc_ut возвращает кортеж, первый элемент - координаты
                        result = swe.calc_ut(julian_day, planet_id)

                        if self._validate_swe_result(result, planet_name):
                            longitude = result[0][0]
                            sign, degree = get_zodiac_sign(longitude)

                            planet_position = PlanetPosition(sign=sign, degree=degree)
                            planets[planet_name] = planet_position

                            logger.debug(
                                f"{planet_name}: {sign} {degree:.2f}° (долгота {longitude:.2f}°)"
                            )
                        else:
                            calculation_errors.append(planet_name)
                            logger.error(
                                f"Не удалось рассчитать позицию для планеты: {planet_name}"
                            )

                    except Exception as e:
                        calculation_errors.append(planet_name)
                        logger.error(f"Ошибка при расчете планеты {planet_name}: {e}")
                        continue
            
            if calculation_errors:
                logger.warning(f"Ошибки при расчете планет: {calculation_errors}")
                
            return planets
        
        try:
            # Выполняем в отдельном потоке с таймаутом
            loop = asyncio.get_event_loop()
            planets = await asyncio.wait_for(
                loop.run_in_executor(None, sync_calculate_planets),
                timeout=30  # Таймаут 30 секунд на расчет всех планет
            )
            return planets
            
        except asyncio.TimeoutError:
            logger.error("Расчет планет превысил таймаут 30 секунд")
            return {}
        except Exception as e:
            logger.error(f"Критическая ошибка асинхронного расчета планет: {e}")
            return {}

    def _validate_planet_positions(self, planets: Dict[str, PlanetPosition]) -> None:
        """Выполняет дополнительную валидацию позиций планет"""
        if not planets:
            logger.warning("Нет планет для валидации")
            return

        # Проверяем, что Меркурий не слишком далеко от Солнца
        if "Солнце" in planets and "Меркурий" in planets:
            sun_pos = (
                Config.ZODIAC_SIGNS.index(planets["Солнце"].sign) * 30
                + planets["Солнце"].degree
            )
            mercury_pos = (
                Config.ZODIAC_SIGNS.index(planets["Меркурий"].sign) * 30
                + planets["Меркурий"].degree
            )

            mercury_distance = min(
                abs(sun_pos - mercury_pos), 360 - abs(sun_pos - mercury_pos)
            )
            if mercury_distance > 28:
                logger.warning(
                    f"Меркурий слишком далеко от Солнца: {mercury_distance:.1f}°"
                )

        # Проверяем, что Венера не слишком далеко от Солнца
        if "Солнце" in planets and "Венера" in planets:
            sun_pos = (
                Config.ZODIAC_SIGNS.index(planets["Солнце"].sign) * 30
                + planets["Солнце"].degree
            )
            venus_pos = (
                Config.ZODIAC_SIGNS.index(planets["Венера"].sign) * 30
                + planets["Венера"].degree
            )

            venus_distance = min(
                abs(sun_pos - venus_pos), 360 - abs(sun_pos - venus_pos)
            )
            if venus_distance > 48:
                logger.warning(
                    f"Венера слишком далеко от Солнца: {venus_distance:.1f}°"
                )

        logger.debug("Валидация позиций планет завершена")


class AstroService:
    """Основной астрологический сервис"""

    def __init__(self):
        self.calculator = AstroCalculator()

    def get_location(self, city_name: str) -> Optional[Location]:
        """Получить информацию о местоположении города"""
        return self.calculator.get_location(city_name)
    
    def validate_city_input(self, city: str) -> tuple[bool, str]:
        """Валидирует ввод города пользователем"""
        return self.calculator.geocoding_service.validate_city_input(city)

    async def calculate_natal_chart(
        self, birth_date: datetime, location: Location
    ) -> Dict[str, PlanetPosition]:
        """Рассчитать натальную карту асинхронно"""
        if not birth_date or not location:
            logger.error("Недостаточно данных для расчета натальной карты")
            return {}

        # Рассчитываем планеты
        planets = await self.calculator.calculate_planets(birth_date, location)
        
        # Добавляем Асцендент
        try:
            from .house_calculator import HouseCalculator
            house_calculator = HouseCalculator()
            
            asc_mc = house_calculator.get_ascendant_midheaven(birth_date, location)
            if asc_mc:
                ascendant_longitude, _ = asc_mc
                ascendant_sign, ascendant_degree = get_zodiac_sign(ascendant_longitude)
                planets["Асцендент"] = PlanetPosition(sign=ascendant_sign, degree=ascendant_degree)
                logger.info(f"Асцендент добавлен: {ascendant_sign} {ascendant_degree:.2f}°")
            else:
                logger.warning("Не удалось рассчитать Асцендент")
        except Exception as e:
            logger.error(f"Ошибка при расчете Асцендента: {e}")

        return planets

    def get_planet_description(self, planet_name: str, sign: str) -> str:
        """Получить описание планеты в знаке из zodiac_data.json"""
        if not planet_name or not sign:
            logger.warning("Неполные данные для получения описания планеты")
            return "Описание недоступно"

        try:
            description = zodiac_data_loader.get_description(planet_name, sign)

            if description:
                logger.debug(f"Получено описание для {planet_name} в {sign}")
                return description
            else:
                logger.warning(
                    f"Не удалось найти описание для {planet_name} в знаке {sign}"
                )
                return f"К сожалению, подробное описание для планеты {planet_name} в знаке {sign} пока отсутствует."

        except Exception as e:
            logger.error(f"Ошибка получения описания планеты: {e}")
            return "Ошибка при получении описания"

    def validate_calculation_quality(
        self, planets: Dict[str, PlanetPosition]
    ) -> Tuple[bool, str]:
        """Оценивает качество астрологических расчетов"""
        if not planets:
            return False, "Планеты не рассчитаны"

        expected_planets = len(AstroCalculator.PLANETS_TO_CALCULATE) + 1  # +1 для Асцендента
        actual_planets = len(planets)

        if actual_planets < expected_planets:
            missing = expected_planets - actual_planets
            return False, f"Отсутствуют {missing} планет из {expected_planets}"

        # Проверяем корректность данных
        for planet_name, position in planets.items():
            if not position.sign or position.sign not in Config.ZODIAC_SIGNS:
                return (
                    False,
                    f"Неверный знак для планеты {planet_name}: {position.sign}",
                )

            if not isinstance(position.degree, (int, float)) or not (
                0 <= position.degree < 30
            ):
                return (
                    False,
                    f"Неверный градус для планеты {planet_name}: {position.degree}",
                )

        return (
            True,
            f"Качество расчетов: отличное ({actual_planets}/{expected_planets} планет)",
        )
