import os
from dataclasses import dataclass
from enum import Enum
from typing import List

from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Config:
    """Класс для хранения конфигурации бота"""

    # Основные настройки бота
    TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    BOT_TOKEN = TOKEN  # Алиас для совместимости
    
    # Проверка обязательных переменных
    if not TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения!")
    
    # Администраторы
    ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
    try:
        ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(",") if admin_id.strip()]
    except (ValueError, TypeError):
        ADMIN_IDS = []
    
    # Если администраторы не указаны, используем хардкод (для совместимости)
    if not ADMIN_IDS:
        ADMIN_IDS = [955128174]  # Ваш ID

    # AI Service
    AI_API = os.getenv("AI_API") or os.getenv("BOTHUB_API_KEY")
    YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
    BOTHUB_API_KEY = AI_API  # Алиас для Bothub

    # База данных
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///astro_bot.db")
    
    # Режим работы
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = ENVIRONMENT == "development"
    
    # Логирование
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Webhook настройки (для продакшена)
    WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
    WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))
    WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
    WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None
    
    # Безопасность
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-me")
    
    # Redis (для кэширования)
    REDIS_URL = os.getenv("REDIS_URL")
    
    # Форматы дат
    DATE_FORMAT = "%d.%m.%Y"
    DATETIME_FORMAT = "%d.%m.%Y %H:%M"

    # Форматы дат для парсинга
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

    # AI сервис настройки
    AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "30"))
    AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "2"))
    AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() in ("true", "1", "yes", "on")
    
    # Лимиты производительности
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Настройки подписки
    SUBSCRIPTION_PRICES = {
        "monthly": {
            "price": int(os.getenv("MONTHLY_PRICE", "499")),
            "currency": os.getenv("CURRENCY", "RUB"),
            "duration_days": 30,
        }
    }
    
    @classmethod
    def get_database_url(cls) -> str:
        """Получить URL базы данных с проверкой"""
        db_url = cls.DATABASE_URL
        
        # Для продакшена рекомендуется PostgreSQL
        if cls.ENVIRONMENT == "production" and db_url.startswith("sqlite"):
            print("⚠️  ПРЕДУПРЕЖДЕНИЕ: Используется SQLite в продакшене. Рекомендуется PostgreSQL.")
        
        return db_url
    
    @classmethod
    def is_production(cls) -> bool:
        """Проверить, запущен ли бот в продакшене"""
        return cls.ENVIRONMENT == "production"
    
    @classmethod
    def get_log_config(cls) -> dict:
        """Получить конфигурацию логирования"""
        return {
            "level": cls.LOG_LEVEL,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "handlers": [
                {
                    "class": "logging.StreamHandler",
                    "level": cls.LOG_LEVEL,
                },
                {
                    "class": "logging.FileHandler",
                    "filename": "logs/bot.log",
                    "level": cls.LOG_LEVEL,
                    "encoding": "utf-8",
                },
            ] if cls.is_production() else [
                {
                    "class": "logging.StreamHandler",
                    "level": cls.LOG_LEVEL,
                }
            ]
        }


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
