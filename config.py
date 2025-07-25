import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Конфигурация приложения"""

    # === TELEGRAM ===
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")
    
    # === ADMIN ===
    ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
    ADMIN_IDS = []
    if ADMIN_IDS_STR:
        try:
            ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(",") if admin_id.strip()]
        except ValueError:
            print("⚠️ Ошибка парсинга ADMIN_IDS, используем пустой список")
            ADMIN_IDS = []

    # === AI ===
    AI_API = os.getenv("AI_API")
    AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "30"))
    AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "3"))

    # === DATABASE ===
    # Поддержка как SQLite для разработки, так и PostgreSQL для продакшена
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Если DATABASE_URL не указан, используем SQLite для разработки
    if not DATABASE_URL:
        DATABASE_URL = "sqlite+aiosqlite:///solarbalance.db"
        print("⚠️ DATABASE_URL не указан, используется SQLite для разработки")
    
    # Определяем тип БД по URL
    IS_POSTGRESQL = DATABASE_URL.startswith(("postgresql://", "postgres://"))
    IS_SQLITE = DATABASE_URL.startswith("sqlite")
    
    if IS_POSTGRESQL:
        print("✅ Используется PostgreSQL")
    elif IS_SQLITE:
        print("✅ Используется SQLite (разработка)")
    else:
        print("⚠️ Неизвестный тип БД, проверьте DATABASE_URL")

    # === SWISS EPHEMERIS ===
    EPHEMERIS_PATH = os.getenv("EPHEMERIS_PATH", ".")

    # === ZODIAC SIGNS ===
    ZODIAC_SIGNS = [
        "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
        "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
    ]

    # === SUBSCRIPTION LIMITS ===
    FREE_USER_LIMITS = {
        "natal_charts": 3,
        "questions_per_day": 5,
        "planets": ["Солнце", "Луна", "Асцендент"]
    }

    PREMIUM_USER_LIMITS = {
        "natal_charts": -1,  # Безлимитно
        "questions_per_day": -1,  # Безлимитно
        "planets": [
            "Солнце", "Луна", "Асцендент", "Меркурий", "Венера", "Марс",
            "Юпитер", "Сатурн", "Уран", "Нептун", "Плутон"
        ]
    }

    # === ANTI-SPAM ===
    ANTI_SPAM_CONFIG = {
        "questions_per_day": 5,
        "premium_questions_per_day": 50,
        "reset_hour": 0,  # Час сброса лимитов (UTC)
    }

    # === LOGGING ===
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # === ENVIRONMENT ===
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    IS_PRODUCTION = ENVIRONMENT.lower() == "production"
    IS_DEVELOPMENT = ENVIRONMENT.lower() == "development"

    # === PERFORMANCE ===
    # Настройки для PostgreSQL
    POSTGRESQL_CONFIG = {
        "pool_size": int(os.getenv("POSTGRESQL_POOL_SIZE", "20")),
        "max_overflow": int(os.getenv("POSTGRESQL_MAX_OVERFLOW", "30")),
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("POSTGRESQL_POOL_RECYCLE", "3600")),
        "echo": os.getenv("POSTGRESQL_ECHO", "false").lower() == "true",
    }

    # Настройки для SQLite
    SQLITE_CONFIG = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "echo": False,
    }

    @classmethod
    def get_database_config(cls) -> dict:
        """Получить конфигурацию БД в зависимости от типа"""
        if cls.IS_POSTGRESQL:
            return cls.POSTGRESQL_CONFIG
        else:
            return cls.SQLITE_CONFIG
    
    @classmethod
    def is_production(cls) -> bool:
        """Проверить, является ли окружение продакшеном"""
        return cls.IS_PRODUCTION

    @classmethod
    def validate_config(cls) -> bool:
        """Проверка корректности конфигурации"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN не указан")
        
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL не указан")
        
        if cls.IS_POSTGRESQL and not cls.AI_API:
            errors.append("AI_API обязателен для продакшена")
        
        if errors:
            print("❌ Ошибки конфигурации:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True

    @classmethod
    def print_config_summary(cls):
        """Вывести краткую сводку конфигурации"""
        print("\n📋 СВОДКА КОНФИГУРАЦИИ:")
        print("=" * 40)
        print(f"🌍 Окружение: {cls.ENVIRONMENT}")
        print(f"🤖 AI API: {'✅ Настроен' if cls.AI_API else '❌ Не настроен'}")
        print(f"🗄️ База данных: {'PostgreSQL' if cls.IS_POSTGRESQL else 'SQLite'}")
        print(f"🔧 Режим: {'Продакшен' if cls.IS_PRODUCTION else 'Разработка'}")
        
        if cls.IS_POSTGRESQL:
            print(f"📊 Пул соединений: {cls.POSTGRESQL_CONFIG['pool_size']}")
            print(f"🔄 Макс. переполнение: {cls.POSTGRESQL_CONFIG['max_overflow']}")
        
        print("=" * 40)


# Валидация конфигурации при импорте
if not Config.validate_config():
    raise RuntimeError("Некорректная конфигурация")

# Вывод сводки конфигурации
Config.print_config_summary()
