import os
from dataclasses import dataclass
from enum import Enum
from typing import List

from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Config:
    """Класс для хранения конфигурации бота"""

    load_dotenv()

    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
    try:
        ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(",") if admin_id]
    except (ValueError, TypeError):
        ADMIN_IDS = []

    # AI Service
    YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
    AI_API = os.getenv("AI_API")  # API ключ для ИИ прогнозов
    BOTHUB_API_KEY = AI_API  # Алиас для Bothub

    # Форматы дат
    DATE_FORMAT = "%d.%m.%Y"
    DATETIME_FORMAT = "%d.%m.%Y %H:%M"

    # Форматы дат
    DATE_TIME_FORMATS = [
        "%d.%m.%Y %H:%M",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M",
        "%Y-%m-%d %H:%M",
    ]

    DATE_ONLY_FORMATS = [
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
    ]

    # Знаки зодиака
    ZODIAC_SIGNS = [
        "Овен",
        "Телец",
        "Близнецы",
        "Рак",
        "Лев",
        "Дева",
        "Весы",
        "Скорпион",
        "Стрелец",
        "Козерог",
        "Водолей",
        "Рыбы",
    ]

    # Список Telegram ID администраторов
    ADMIN_IDS = [
        955128174,  # Ваш ID
        # Добавьте сюда ID администраторов в числовом формате
        # Например: 123456789, 987654321
    ]

    # AI сервис настройки (максимальная стабильность)
    AI_REQUEST_TIMEOUT = 30  # секунд для AI запросов (максимальный таймаут)
    AI_MAX_RETRIES = 2  # максимум попыток при ошибке
    AI_ENABLED = True  # ВКЛЮЧЕН - API работает стабильно


class Planets(Enum):
    """Планеты для расчетов"""

    SUN = (0, "Солнце")
    MOON = (1, "Луна")
    MERCURY = (2, "Меркурий")
    VENUS = (3, "Венера")
    MARS = (4, "Марс")
    JUPITER = (5, "Юпитер")
    SATURN = (6, "Сатурн")
    URANUS = (7, "Уран")
    NEPTUNE = (8, "Нептун")
    PLUTO = (9, "Плутон")
