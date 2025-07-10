import logging
import threading
import zoneinfo
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import swisseph as swe

from config import Config
from models import Location

logger = logging.getLogger(__name__)

# Глобальная блокировка для Swiss Ephemeris (не потокобезопасен)
swe_lock = threading.Lock()


class TransitCalculator:
    """Калькулятор транзитов"""

    def __init__(self):
        # Планеты для расчета транзитов (исключаем Лилит и другие астероиды для базовой версии)
        self.transit_planets = {
            swe.SUN: "Солнце",
            swe.MOON: "Луна",
            swe.MERCURY: "Меркурий",
            swe.VENUS: "Венера",
            swe.MARS: "Марс",
            swe.JUPITER: "Юпитер",
            swe.SATURN: "Сатурн",
            swe.URANUS: "Уран",
            swe.NEPTUNE: "Нептун",
            swe.PLUTO: "Плутон",
        }

        # Настройки аспектов для транзитов
        self.transit_aspects = {
            "conjunction": {"angle": 0, "name": "соединение", "symbol": "☌"},
            "opposition": {"angle": 180, "name": "оппозиция", "symbol": "☍"},
            "square": {"angle": 90, "name": "квадрат", "symbol": "□"},
            "trine": {"angle": 120, "name": "трин", "symbol": "△"},
            "sextile": {"angle": 60, "name": "секстиль", "symbol": "⚹"},
        }

        # Орбы для транзитов (меньше чем для натальных аспектов)
        self.transit_orbs = {
            "Солнце": {
                "conjunction": 1.0,
                "opposition": 1.0,
                "square": 0.8,
                "trine": 0.8,
                "sextile": 0.6,
            },
            "Луна": {
                "conjunction": 1.0,
                "opposition": 1.0,
                "square": 0.8,
                "trine": 0.8,
                "sextile": 0.6,
            },
            "Меркурий": {
                "conjunction": 0.8,
                "opposition": 0.8,
                "square": 0.6,
                "trine": 0.6,
                "sextile": 0.5,
            },
            "Венера": {
                "conjunction": 0.8,
                "opposition": 0.8,
                "square": 0.6,
                "trine": 0.6,
                "sextile": 0.5,
            },
            "Марс": {
                "conjunction": 0.8,
                "opposition": 0.8,
                "square": 0.6,
                "trine": 0.6,
                "sextile": 0.5,
            },
            "Юпитер": {
                "conjunction": 1.0,
                "opposition": 1.0,
                "square": 0.8,
                "trine": 0.8,
                "sextile": 0.6,
            },
            "Сатурн": {
                "conjunction": 1.0,
                "opposition": 1.0,
                "square": 0.8,
                "trine": 0.8,
                "sextile": 0.6,
            },
            "Уран": {
                "conjunction": 0.8,
                "opposition": 0.8,
                "square": 0.6,
                "trine": 0.6,
                "sextile": 0.5,
            },
            "Нептун": {
                "conjunction": 0.8,
                "opposition": 0.8,
                "square": 0.6,
                "trine": 0.6,
                "sextile": 0.5,
            },
            "Плутон": {
                "conjunction": 0.8,
                "opposition": 0.8,
                "square": 0.6,
                "trine": 0.6,
                "sextile": 0.5,
            },
        }

    def _normalize_angle(self, angle: float) -> float:
        """Нормализует угол к диапазону 0-360°"""
        while angle < 0:
            angle += 360
        while angle >= 360:
            angle -= 360
        return angle

    def _calculate_angular_distance(self, pos1: float, pos2: float) -> float:
        """Рассчитывает угловое расстояние между двумя позициями"""
        diff = abs(pos1 - pos2)
        return min(diff, 360 - diff)

    def _get_orb_for_transit(self, transit_planet: str, aspect_type: str) -> float:
        """Получает орб для транзитного аспекта"""
        planet_orbs = self.transit_orbs.get(transit_planet, self.transit_orbs["Плутон"])
        return planet_orbs.get(aspect_type, 0.5)

    def _calculate_planet_speed(
        self, planet_id: int, julian_day: float
    ) -> Optional[float]:
        """Рассчитывает скорость планеты (градусов в день)"""
        try:
            with swe_lock:
                # Рассчитываем позицию сегодня
                today_result = swe.calc_ut(julian_day, planet_id)
                if not today_result or len(today_result[0]) < 3:
                    return None

                today_pos = today_result[0][0]
                today_speed = today_result[0][3]  # Скорость в градусах/день

                return today_speed

        except Exception as e:
            logger.warning(f"Ошибка расчета скорости планеты {planet_id}: {e}")
            return None

    def _is_planet_retrograde(self, planet_id: int, julian_day: float) -> bool:
        """Определяет, является ли планета ретроградной"""
        speed = self._calculate_planet_speed(planet_id, julian_day)
        return speed is not None and speed < 0

    def get_current_transits(self, birth_dt: datetime, location: Location) -> List[str]:
        """Получает текущие транзиты"""
        logger.info(f"Расчет текущих транзитов для даты рождения {birth_dt}")

        try:
            with swe_lock:
                # Получаем текущую дату
                now = datetime.now(zoneinfo.ZoneInfo(location.timezone))

                # Рассчитываем позиции планет на момент рождения
                natal_planets = self._calculate_natal_planets(birth_dt, location)
                if not natal_planets:
                    logger.warning("Не удалось рассчитать натальные позиции планет")
                    return []

                # Рассчитываем текущие позиции планет
                current_planets = self._calculate_current_planets(now, location)
                if not current_planets:
                    logger.warning("Не удалось рассчитать текущие позиции планет")
                    return []

                # Анализируем аспекты между транзитными и натальными планетами
                transits = self._analyze_transits_improved(
                    natal_planets, current_planets, now
                )

                logger.info(f"Найдено {len(transits)} активных транзитов")
                return transits

        except Exception as e:
            logger.error(f"Ошибка расчета транзитов: {e}")
            return []

    def _calculate_natal_planets(
        self, birth_dt: datetime, location: Location
    ) -> Dict[str, float]:
        """Рассчитывает позиции планет на момент рождения"""
        planets = {}

        try:
            # Переводим время в UTC
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

            # Рассчитываем позиции планет
            for planet_id, planet_name in self.transit_planets.items():
                try:
                    result = swe.calc_ut(julian_day, planet_id)
                    if result and len(result[0]) > 0:
                        longitude = self._normalize_angle(
                            result[0][0]
                        )  # Эклиптическая долгота
                        planets[planet_name] = longitude
                except Exception as e:
                    logger.warning(f"Ошибка расчета натального {planet_name}: {e}")
                    continue

            return planets

        except Exception as e:
            logger.error(f"Ошибка расчета натальных планет: {e}")
            return {}

    def _calculate_current_planets(
        self, current_dt: datetime, location: Location
    ) -> Dict[str, Tuple[float, bool]]:
        """Рассчитывает текущие позиции планет с информацией о ретроградности"""
        planets = {}

        try:
            # Переводим время в UTC
            utc_dt = current_dt.astimezone(zoneinfo.ZoneInfo("UTC"))

            # Юлианская дата
            julian_day = swe.julday(
                utc_dt.year,
                utc_dt.month,
                utc_dt.day,
                utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
            )

            # Рассчитываем позиции планет
            for planet_id, planet_name in self.transit_planets.items():
                try:
                    result = swe.calc_ut(julian_day, planet_id)
                    if result and len(result[0]) > 0:
                        longitude = self._normalize_angle(
                            result[0][0]
                        )  # Эклиптическая долгота
                        is_retrograde = self._is_planet_retrograde(
                            planet_id, julian_day
                        )
                        planets[planet_name] = (longitude, is_retrograde)
                except Exception as e:
                    logger.warning(f"Ошибка расчета текущего {planet_name}: {e}")
                    continue

            return planets

        except Exception as e:
            logger.error(f"Ошибка расчета текущих планет: {e}")
            return {}

    def _analyze_transits_improved(
        self,
        natal_planets: Dict[str, float],
        current_planets: Dict[str, Tuple[float, bool]],
        current_dt: datetime,
    ) -> List[str]:
        """Улучшенный анализ транзитов с учетом ретроградности и переменных орбов"""
        transits = []

        # Анализируем аспекты между транзитными и натальными планетами
        for transit_planet, (transit_pos, is_retrograde) in current_planets.items():
            for natal_planet, natal_pos in natal_planets.items():

                # Рассчитываем угол между планетами
                angle = self._calculate_angular_distance(transit_pos, natal_pos)

                # Проверяем различные аспекты
                for aspect_key, aspect_info in self.transit_aspects.items():
                    target_angle = aspect_info["angle"]
                    orb_deviation = abs(angle - target_angle)
                    max_orb = self._get_orb_for_transit(transit_planet, aspect_key)

                    if orb_deviation <= max_orb:
                        # Определяем качество аспекта
                        strength = ((max_orb - orb_deviation) / max_orb) * 100

                        # Определяем точность описания
                        if strength >= 90:
                            precision = "точный"
                        elif strength >= 70:
                            precision = "тесный"
                        elif strength >= 50:
                            precision = "средний"
                        else:
                            precision = "широкий"

                        # Формируем описание транзита
                        retrograde_mark = " (R)" if is_retrograde else ""
                        symbol = aspect_info["symbol"]

                        transit_desc = (
                            f"{transit_planet}{retrograde_mark} {symbol} натальный {natal_planet} "
                            f"({aspect_info['name']}, {precision}, орб {orb_deviation:.1f}°)"
                        )

                        transits.append(
                            {
                                "description": transit_desc,
                                "strength": strength,
                                "transit_planet": transit_planet,
                                "natal_planet": natal_planet,
                                "aspect": aspect_info["name"],
                                "orb": orb_deviation,
                                "is_retrograde": is_retrograde,
                            }
                        )
                        break  # Нашли аспект, переходим к следующей паре

        # Сортируем по силе аспекта
        transits.sort(key=lambda x: x["strength"], reverse=True)

        # Возвращаем только описания, ограничиваем количество
        return [t["description"] for t in transits[:12]]

    def get_transit_summary(self, birth_dt: datetime, location: Location) -> str:
        """Возвращает краткое описание текущих транзитов"""
        transits = self.get_current_transits(birth_dt, location)

        if not transits:
            return "В данный момент нет активных значимых транзитов."

        summary = "🌟 Текущие астрологические транзиты:\n\n"
        for i, transit in enumerate(transits[:8], 1):  # Показываем максимум 8
            summary += f"{i}. {transit}\n"

        if len(transits) > 8:
            summary += f"\n... и еще {len(transits) - 8} транзитов"

        return summary

    def get_retrograde_info(self) -> str:
        """Получает информацию о ретроградных планетах (на текущий момент)"""
        try:
            current_date = datetime.now(zoneinfo.ZoneInfo("UTC"))
            retrograde_planets = []

            with swe_lock:
                # Рассчитываем юлианскую дату для текущего момента
                julian_day = swe.julday(
                    current_date.year,
                    current_date.month,
                    current_date.day,
                    current_date.hour + current_date.minute / 60.0,
                )

                # Проверяем каждую планету на ретроградность
                for planet_id, planet_name in self.transit_planets.items():
                    if planet_name in [
                        "Солнце",
                        "Луна",
                    ]:  # Солнце и Луна никогда не бывают ретроградными
                        continue

                    try:
                        if self._is_planet_retrograde(planet_id, julian_day):
                            retrograde_planets.append(planet_name)
                    except Exception as e:
                        logger.warning(
                            f"Ошибка проверки ретроградности {planet_name}: {e}"
                        )
                        continue

            if not retrograde_planets:
                return "В настоящее время нет ретроградных планет."

            return f"Ретроградные планеты: {', '.join(retrograde_planets)}"

        except Exception as e:
            logger.error(f"Ошибка получения информации о ретроградных планетах: {e}")
            return "Не удалось получить информацию о ретроградных планетах."

    def calculate_daily_transits(
        self, birth_dt: datetime, location: Location, target_date: datetime = None
    ) -> List[str]:
        """Рассчитывает транзиты на конкретную дату"""
        if target_date is None:
            target_date = datetime.now(zoneinfo.ZoneInfo(location.timezone))

        logger.info(f"Расчет транзитов на {target_date.date()}")

        try:
            # Получаем натальные позиции
            natal_planets = self._calculate_natal_planets(birth_dt, location)
            if not natal_planets:
                return []

            # Получаем позиции планет на целевую дату
            target_planets = self._calculate_current_planets(target_date, location)
            if not target_planets:
                return []

            # Анализируем транзиты
            transits = self._analyze_transits_improved(
                natal_planets, target_planets, target_date
            )

            return transits

        except Exception as e:
            logger.error(f"Ошибка расчета дневных транзитов: {e}")
            return []

    def get_transit_trends(
        self, birth_dt: datetime, location: Location, days_ahead: int = 7
    ) -> Dict[str, List[str]]:
        """Получает тенденции транзитов на несколько дней вперед"""
        trends = {}
        current_date = datetime.now(zoneinfo.ZoneInfo(location.timezone))

        for i in range(days_ahead):
            target_date = current_date + timedelta(days=i)
            date_key = target_date.strftime("%Y-%m-%d")
            trends[date_key] = self.calculate_daily_transits(
                birth_dt, location, target_date
            )

        return trends
