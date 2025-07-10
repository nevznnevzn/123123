"""
Упрощенная версия главного файла астрологического бота.
Принцип KISS: минимум кода, максимум функциональности.
"""

import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from database_async import async_db_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def setup_bot() -> tuple[Bot, Dispatcher]:
    """Простая настройка бота и диспетчера"""
    # Создаем бота
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Создаем диспетчер с хранилищем в памяти
    dp = Dispatcher(storage=MemoryStorage())
    
    # Передаем глобальные объекты
    dp["db_manager"] = async_db_manager
    dp["bot"] = bot
    
    return bot, dp


async def register_handlers(dp: Dispatcher) -> None:
    """Регистрация всех хэндлеров"""
    # Импорты здесь для избежания циклических зависимостей
    from handlers.common.router import common_router
    from handlers.profile.router import profile_router
    from handlers.natal_chart.router import natal_chart_router
    from handlers.predictions.router import predictions_router
    from handlers.compatibility.router import compatibility_router
    from handlers.sky_map.router import sky_map_router
    from handlers.star_advice.router import star_advice_router
    from handlers.admin.router import create_admin_router
    
    # Регистрируем роутеры в порядке приоритета
    dp.include_router(common_router)
    dp.include_router(profile_router)
    dp.include_router(natal_chart_router)
    dp.include_router(predictions_router)
    dp.include_router(compatibility_router)
    dp.include_router(sky_map_router)
    dp.include_router(star_advice_router)
    dp.include_router(create_admin_router())


async def setup_database() -> None:
    """Инициализация базы данных"""
    try:
        await async_db_manager.init_db()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        sys.exit(1)


async def startup_tasks() -> None:
    """Задачи при запуске бота"""
    await setup_database()
    
    # Очищаем устаревшие прогнозы
    try:
        deleted = await async_db_manager.cleanup_expired_predictions()
        if deleted > 0:
            logger.info(f"Удалено {deleted} устаревших прогнозов")
    except Exception as e:
        logger.warning(f"Ошибка очистки прогнозов: {e}")


async def shutdown_tasks() -> None:
    """Задачи при остановке бота"""
    try:
        await async_db_manager.close()
        logger.info("Соединение с БД закрыто")
    except Exception as e:
        logger.error(f"Ошибка закрытия БД: {e}")


async def main() -> None:
    """Главная функция запуска бота"""
    logger.info("Запуск астрологического бота...")
    
    try:
        # Настройка компонентов
        bot, dp = await setup_bot()
        await register_handlers(dp)
        
        # Задачи при запуске
        await startup_tasks()
        
        # Запуск бота
        logger.info("Бот запущен и готов к работе")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)
    
    finally:
        # Задачи при остановке
        await shutdown_tasks()


if __name__ == "__main__":
    # Простой запуск без лишних проверок
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        sys.exit(1) 