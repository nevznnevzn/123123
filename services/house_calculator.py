import logging
import threading
import zoneinfo
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import swisseph as swe

from config import Config
from models import Location, PlanetPosition

logger = logging.getLogger(__name__)

# Глобальная блокировка для Swiss Ephemeris (не потокобезопасен)
swe_lock = threading.Lock()


class HouseCalculator:
    """Калькулятор астрологических домов"""

    def __init__(self):
        # Импортируем AspectCalculator здесь чтобы избежать циклических импортов
        from .aspect_calculator import AspectCalculator

        self.aspect_calculator = AspectCalculator()

    def _normalize_longitude(self, longitude: float) -> float:
        """Нормализует долготу к диапазону 0-360°"""
        while longitude < 0:
            longitude += 360
        while longitude >= 360:
            longitude -= 360
        return longitude

    def _is_planet_in_house(
        self, planet_longitude: float, house_start: float, house_end: float
    ) -> bool:
        """
        Проверяет, находится ли планета в доме с учетом пересечения 0° Овна.

        Args:
            planet_longitude: Долгота планеты (0-360°)
            house_start: Начало дома (0-360°)
            house_end: Конец дома (0-360°)

        Returns:
            True если планета в доме
        """
        # Нормализуем все значения
        planet_longitude = self._normalize_longitude(planet_longitude)
        house_start = self._normalize_longitude(house_start)
        house_end = self._normalize_longitude(house_end)

        # Случай 1: Дом не пересекает 0° (например, от 30° до 60°)
        if house_start < house_end:
            return house_start <= planet_longitude < house_end

        # Случай 2: Дом пересекает 0° Овна (например, от 330° до 30°)
        else:
            return planet_longitude >= house_start or planet_longitude < house_end

    def _calculate_house_span_degrees(
        self, house_start: float, house_end: float
    ) -> float:
        """Рассчитывает размер дома в градусах"""
        house_start = self._normalize_longitude(house_start)
        house_end = self._normalize_longitude(house_end)

        if house_start < house_end:
            return house_end - house_start
        else:
            return (360 - house_start) + house_end

    def get_houses_info(
        self,
        planets: Dict[str, PlanetPosition],
        birth_dt: datetime = None,
        location: Location = None,
    ) -> str:
        """Формирует информацию о домах с использованием точных астрологических расчетов"""
        if not birth_dt or not location:
            logger.warning("Отсутствуют данные для расчета домов")
            return ""

        try:
            house_cusps = self.calculate_house_positions(birth_dt, location)
            if not house_cusps or len(house_cusps) < 12:
                logger.warning("Не удалось получить куспиды домов")
                return ""

            # Определяем планеты в домах
            houses_info = []

            for house_num in range(1, 13):
                house_start = house_cusps[house_num - 1]
                house_end = house_cusps[
                    house_num % 12
                ]  # Используем % для перехода от 12-го к 1-му дому

                planets_in_house = []

                for planet_name, position in planets.items():
                    if planet_name == "Асцендент":
                        continue

                    # Переводим позицию планеты в градусы от 0° Овна
                    planet_longitude = (
                        self.aspect_calculator._sign_to_degrees(position.sign)
                        + position.degree
                    )

                    # Проверяем, попадает ли планета в дом
                    if self._is_planet_in_house(
                        planet_longitude, house_start, house_end
                    ):
                        planets_in_house.append(planet_name)

                if planets_in_house:
                    # Определяем знак на куспиде дома
                    cusp_sign_index = (
                        int(self._normalize_longitude(house_start) // 30) % 12
                    )
                    cusp_sign = Config.ZODIAC_SIGNS[cusp_sign_index]
                    cusp_degree = house_start % 30

                    house_span = self._calculate_house_span_degrees(
                        house_start, house_end
                    )
                    houses_info.append(
                        f"{house_num} дом ({cusp_sign} {cusp_degree:.1f}°, размер {house_span:.1f}°): {', '.join(planets_in_house)}"
                    )

            return (
                "\n• ".join(houses_info)
                if houses_info
                else "Планеты в домах не обнаружены"
            )

        except Exception as e:
            logger.error(f"Ошибка расчета домов: {e}")
            return ""

    def calculate_house_positions(
        self, birth_dt: datetime, location: Location
    ) -> List[float]:
        """Рассчитывает куспиды всех 12 домов"""
        house_cusps = []

        try:
            with swe_lock:
                # Переводим время в UTC если нужно
                if birth_dt.tzinfo is None:
                    tz = zoneinfo.ZoneInfo(location.timezone)
                    birth_dt = birth_dt.replace(tzinfo=tz)

                utc_dt = birth_dt.astimezone(zoneinfo.ZoneInfo("UTC"))

                # Юлианская дата
                julian_day = swe.julday(
                    utc_dt.year,
                    utc_dt.month,
                    utc_dt.day,
                    utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
                )

                # Проверяем экстремальные широты
                if abs(location.lat) > 66.5:
                    logger.warning(
                        f"Расчет домов на экстремальной широте {location.lat}° может быть неточным"
                    )

                # Рассчитываем дома по системе Плацидуса
                houses_result = swe.houses(julian_day, location.lat, location.lng, b"P")

                if not houses_result or len(houses_result) < 2:
                    logger.error("Swiss Ephemeris не вернул данные о домах")
                    return []

                cusps = houses_result[0]
                ascmc = houses_result[1]  # Асцендент, МС и другие точки

                if len(cusps) < 12:
                    logger.error(f"Получено недостаточно куспидов: {len(cusps)}")
                    return []

                # Нормализуем куспиды и проверяем их валидность
                house_cusps = []
                for i in range(12):
                    cusp = self._normalize_longitude(cusps[i])
                    house_cusps.append(cusp)

                # Дополнительная валидация: проверяем, что дома идут по порядку
                self._validate_house_sequence(house_cusps)

                logger.info(
                    f"Успешно рассчитаны куспиды домов. АСЦ: {ascmc[0]:.1f}°, МС: {ascmc[1]:.1f}°"
                )
                return house_cusps

        except Exception as e:
            logger.error(f"Ошибка расчета куспидов домов: {e}")
            return []

    def _validate_house_sequence(self, house_cusps: List[float]) -> None:
        """Валидирует последовательность куспидов домов"""
        if len(house_cusps) != 12:
            raise ValueError(f"Неверное количество куспидов: {len(house_cusps)}")

        # Проверяем, что куспиды домов идут в правильном порядке (против часовой стрелки)
        for i in range(12):
            current_cusp = house_cusps[i]
            next_cusp = house_cusps[(i + 1) % 12]

            # Рассчитываем размер дома
            house_size = self._calculate_house_span_degrees(current_cusp, next_cusp)

            # Дом не может быть меньше 5° или больше 60° (аномально большой)
            if house_size < 5 or house_size > 60:
                logger.warning(f"Дом {i+1} имеет аномальный размер: {house_size:.1f}°")

    def get_planets_in_houses(
        self, planets: Dict[str, PlanetPosition], house_cusps: List[float]
    ) -> Dict[int, List[str]]:
        """Определяет, в каких домах находятся планеты"""
        planets_by_house = {}

        if len(house_cusps) < 12:
            logger.error("Недостаточно куспидов для расчета")
            return planets_by_house

        for house_num in range(1, 13):
            house_start = house_cusps[house_num - 1]
            house_end = house_cusps[house_num % 12]

            planets_in_house = []

            for planet_name, position in planets.items():
                if planet_name == "Асцендент":
                    continue

                # Переводим позицию планеты в градусы от 0° Овна
                planet_longitude = (
                    self.aspect_calculator._sign_to_degrees(position.sign)
                    + position.degree
                )

                # Проверяем, попадает ли планета в дом
                if self._is_planet_in_house(planet_longitude, house_start, house_end):
                    planets_in_house.append(planet_name)

            if planets_in_house:
                planets_by_house[house_num] = planets_in_house

        return planets_by_house

    def calculate_houses(
        self, birth_dt: datetime, location: Location
    ) -> Dict[int, dict]:
        """Рассчитывает астрологические дома"""
        logger.info(f"Расчет астрологических домов для {birth_dt} в {location.city}")

        try:
            # Получаем куспиды домов
            house_cusps = self.calculate_house_positions(birth_dt, location)

            if not house_cusps or len(house_cusps) < 12:
                logger.warning("Не удалось получить куспиды домов")
                return {}

            # Формируем результат с подробной информацией о каждом доме
            houses_info = {}

            for house_num in range(1, 13):
                house_start = house_cusps[house_num - 1]
                house_end = house_cusps[house_num % 12]

                # Определяем знак на куспиде дома
                normalized_start = self._normalize_longitude(house_start)
                cusp_sign_index = int(normalized_start // 30) % 12
                cusp_sign = Config.ZODIAC_SIGNS[cusp_sign_index]
                cusp_degree = normalized_start % 30

                house_span = self._calculate_house_span_degrees(house_start, house_end)

                houses_info[house_num] = {
                    "cusp_longitude": house_start,
                    "cusp_sign": cusp_sign,
                    "cusp_degree": cusp_degree,
                    "end_longitude": house_end,
                    "house_span_degrees": house_span,
                    "planets": [],  # Будет заполнено позже при расчете натальной карты
                }

            logger.info(f"Успешно рассчитаны {len(houses_info)} домов")
            return houses_info

        except Exception as e:
            logger.error(f"Ошибка расчета домов: {e}")
            return {}

    def get_ascendant_midheaven(
        self, birth_dt: datetime, location: Location
    ) -> Optional[Tuple[float, float]]:
        """Получает точные координаты Асцендента и Середины Неба"""
        try:
            with swe_lock:
                if birth_dt.tzinfo is None:
                    tz = zoneinfo.ZoneInfo(location.timezone)
                    birth_dt = birth_dt.replace(tzinfo=tz)

                utc_dt = birth_dt.astimezone(zoneinfo.ZoneInfo("UTC"))
                julian_day = swe.julday(
                    utc_dt.year,
                    utc_dt.month,
                    utc_dt.day,
                    utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
                )

                houses_result = swe.houses(julian_day, location.lat, location.lng, b"P")
                if houses_result and len(houses_result) >= 2:
                    ascmc = houses_result[1]
                    ascendant = self._normalize_longitude(ascmc[0])  # Асцендент
                    midheaven = self._normalize_longitude(ascmc[1])  # МС

                    logger.info(f"АСЦ: {ascendant:.2f}°, МС: {midheaven:.2f}°")
                    return ascendant, midheaven

        except Exception as e:
            logger.error(f"Ошибка расчета Асцендента/МС: {e}")

        return None
