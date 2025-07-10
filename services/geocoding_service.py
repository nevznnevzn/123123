import logging
import re
import zoneinfo
from datetime import datetime
from typing import Optional

import geopy.geocoders
import timezonefinder

from config import Config
from models import Location

logger = logging.getLogger(__name__)


class GeocodingService:
    """Сервис геокодирования"""

    def __init__(self):
        # Инициализируем геокодер Nominatim (OpenStreetMap)
        self.geolocator = geopy.geocoders.Nominatim(
            user_agent="solarbalance_astro_bot", timeout=10
        )
        # Инициализируем определитель часовых поясов
        self.tf = timezonefinder.TimezoneFinder()

    def validate_city_input(self, city: str) -> tuple[bool, str]:
        """
        Валидирует ввод города пользователем
        Возвращает (is_valid, error_message)
        """
        if not city or not isinstance(city, str):
            return False, "Название города не может быть пустым"
        
        city = city.strip()
        
        # Проверяем минимальную длину
        if len(city) < 2:
            return False, "Название города слишком короткое (минимум 2 символа)"
        
        # Проверяем максимальную длину
        if len(city) > 100:
            return False, "Название города слишком длинное (максимум 100 символов)"
        
        # Проверяем, что это не только числа
        if city.isdigit():
            return False, "Название города не может состоять только из цифр"
        
        # Проверяем, что нет слишком много цифр (больше 30% от длины, но не более 3 цифр)
        digit_count = sum(1 for char in city if char.isdigit())
        if digit_count > 3 or (digit_count > len(city) * 0.3 and len(city) > 5):
            return False, "В названии города слишком много цифр"
        
        # Проверяем недопустимые символы (буквы любых языков, цифры, пробелы, дефисы, апострофы и точки)
        if not re.match(r"^[\w\s\-'.àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]+$", city, re.UNICODE):
            return False, "Название города содержит недопустимые символы"
        
        # Проверяем, что не состоит только из специальных символов
        if re.match(r"^[\s\-'.]+$", city):
            return False, "Название города не может состоять только из пробелов и знаков"
        
        # Проверяем на очевидно недопустимые варианты
        suspicious_patterns = [
            r"^[0-9]+$",  # только цифры
            r"^[^a-zA-Zа-яёА-ЯЁ]+$",  # без букв вообще
            r"^(.)\1{4,}$",  # повторение одного символа 5+ раз
            r"^(test|тест|123|111|222|333|qwe|asd|zxc|qwerty|asdf|йцукен)$",  # тестовые значения и клавиатурные комбинации
        ]
        
        for pattern in suspicious_patterns:
            if re.match(pattern, city, re.IGNORECASE):
                return False, "Введите настоящее название города"
        
        return True, ""

    def get_coordinates(self, city: str) -> Optional[dict]:
        """Получает координаты города"""
        try:
            # Валидируем ввод города
            is_valid, error_message = self.validate_city_input(city)
            if not is_valid:
                logger.warning(f"Невалидный ввод города: {city} - {error_message}")
                return None

            logger.info(f"Геокодирование города: {city}")

            # Ищем локацию через Nominatim
            location = self.geolocator.geocode(city, language="ru")
            if not location:
                logger.warning(f"Город не найден: {city}")
                return None

            # Определяем часовой пояс
            timezone = self.tf.timezone_at(
                lat=location.latitude, lng=location.longitude
            )

            result = {
                "city": city,
                "lat": location.latitude,
                "lng": location.longitude,
                "timezone": timezone or "UTC",
                "address": location.address,
            }

            logger.info(
                f"Геокодирование успешно: {city} -> {result['lat']:.4f}, {result['lng']:.4f}, {result['timezone']}"
            )
            return result

        except Exception as e:
            logger.error(f"Ошибка геокодирования города {city}: {e}")
            return None

    def get_location(self, city_name: str) -> Optional[Location]:
        """Получает координаты и часовой пояс города"""
        coords = self.get_coordinates(city_name)
        if not coords:
            return None

        return Location(
            city=coords["city"],
            lat=coords["lat"],
            lng=coords["lng"],
            timezone=coords["timezone"],
        )

    def parse_datetime(self, text: str, timezone_str: str) -> Optional[datetime]:
        """Парсит дату и время"""
        text = text.strip()

        # Проверяем форматы с временем
        for fmt in Config.DATE_TIME_FORMATS:
            try:
                dt = datetime.strptime(text, fmt)
                tz = zoneinfo.ZoneInfo(timezone_str)
                return dt.replace(tzinfo=tz)
            except (ValueError, zoneinfo.ZoneInfoNotFoundError):
                continue

        # Проверяем форматы без времени
        for fmt in Config.DATE_ONLY_FORMATS:
            try:
                dt = datetime.strptime(text, fmt)
                dt = dt.replace(hour=12, minute=0)
                tz = zoneinfo.ZoneInfo(timezone_str)
                return dt.replace(tzinfo=tz)
            except (ValueError, zoneinfo.ZoneInfoNotFoundError):
                continue

        return None
