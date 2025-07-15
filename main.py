import asyncio
import logging
import sys
import signal
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from config import Config
from database import DatabaseManager
from services.motivation_service import send_daily_motivation
from utils import set_bot_commands


# Настройка логирования
def setup_logging():
    """Настройка логирования для продакшена"""
    
    # Создаем директорию для логов
    Path("logs").mkdir(exist_ok=True)
    
    # Базовая конфигурация
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    
    # Настройка root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/bot.log", encoding="utf-8") if Config.is_production() else logging.NullHandler()
        ]
    )
    
    # Отключаем слишком подробные логи сторонних библиотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


# Глобальные переменные для graceful shutdown
bot_instance = None
dp_instance = None
scheduler_instance = None


async def shutdown_handler(signal_name: str):
    """Обработчик graceful shutdown"""
    logger = logging.getLogger(__name__)
    logger.info(f"🛑 Получен сигнал {signal_name}, начинаем graceful shutdown...")
    
    try:
        # Останавливаем планировщик
        if scheduler_instance:
            scheduler_instance.shutdown()
            logger.info("✅ Планировщик остановлен")
        
        # Останавливаем диспетчер
        if dp_instance:
            await dp_instance.stop_polling()
            logger.info("✅ Диспетчер остановлен")
        
        # Закрываем сессию бота
        if bot_instance:
            await bot_instance.session.close()
            logger.info("✅ Сессия бота закрыта")
            
        logger.info("✅ Graceful shutdown завершен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при shutdown: {e}")
    
    finally:
        # Принудительно завершаем процесс
        sys.exit(0)


def setup_signal_handlers():
    """Настройка обработчиков сигналов"""
    if sys.platform != "win32":  # Unix-like системы
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda s, f: asyncio.create_task(shutdown_handler(signal.Signals(s).name)))


async def main():
    """Основная функция для запуска бота"""
    
    # Настройка логирования
    logger = setup_logging()
    
    logger.info("🚀 Запуск SolarBalance бота...")
    logger.info(f"📊 Режим работы: {Config.ENVIRONMENT}")
    logger.info(f"🗄️ База данных: {Config.get_database_url()}")
    logger.info(f"🤖 AI включен: {Config.AI_ENABLED}")
    
    # Глобальные переменные
    global bot_instance, dp_instance, scheduler_instance
    
    try:
        # --- Инициализация ---
        storage = MemoryStorage()
        
        # База данных с проверкой
        try:
            db_manager = DatabaseManager(Config.get_database_url())
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            raise
        
        # Бот
        try:
            bot_instance = Bot(
                token=Config.TOKEN, 
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            logger.info("✅ Бот инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации бота: {e}")
            raise
        
        # Диспетчер
        dp_instance = Dispatcher(storage=storage, db_manager=db_manager, bot=bot_instance)
        
        # --- Импорты роутеров ---
        try:
            from handlers.admin.middlewares import AdminAuthMiddleware
            from handlers.admin.router import create_admin_router
            from handlers.common.router import router as common_router
            from handlers.compatibility.router import router as compatibility_router
            from handlers.natal_chart.router import create_natal_chart_router
            from handlers.predictions.router import router as predictions_router
            from handlers.profile.router import create_profile_router
            from handlers.sky_map.router import router as sky_map_router
            from handlers.star_advice.router import router as star_advice_router
            from handlers.subscription.router import router as subscription_router
            from services.astro_calculations import AstroService
            from services.subscription_service import SubscriptionService
            
            logger.info("✅ Модули импортированы")
        except Exception as e:
            logger.error(f"❌ Ошибка импорта модулей: {e}")
            raise

        # --- Инициализация сервисов ---
        try:
            astro_service = AstroService()
            subscription_service = SubscriptionService()
            logger.info("✅ Сервисы инициализированы")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации сервисов: {e}")
            raise

        # --- Регистрация роутеров ---
        try:
            # Админ роутер с middleware
            admin_router = create_admin_router()
            auth_middleware = AdminAuthMiddleware(admin_ids=Config.ADMIN_IDS)
            admin_router.message.middleware(auth_middleware)
            admin_router.callback_query.middleware(auth_middleware)
            dp_instance.include_router(admin_router)

            # Основные роутеры
            dp_instance.include_router(
                create_profile_router(db_manager=db_manager, astro_service=astro_service)
            )
            dp_instance.include_router(
                create_natal_chart_router(
                    db_manager=db_manager,
                    astro_service=astro_service,
                    subscription_service=subscription_service,
                )
            )
            dp_instance.include_router(predictions_router)
            dp_instance.include_router(compatibility_router)
            dp_instance.include_router(star_advice_router)
            dp_instance.include_router(sky_map_router)
            dp_instance.include_router(subscription_router)
            dp_instance.include_router(common_router)
            
            logger.info("✅ Роутеры зарегистрированы")
        except Exception as e:
            logger.error(f"❌ Ошибка регистрации роутеров: {e}")
            raise

        # --- Настройка команд ---
        try:
            await set_bot_commands(bot_instance)
            logger.info("✅ Команды бота установлены")
        except Exception as e:
            logger.error(f"❌ Ошибка установки команд: {e}")
            # Не критично, продолжаем

        # --- Планировщик ---
        try:
            scheduler_instance = AsyncIOScheduler(timezone=timezone("Europe/Moscow"))
            scheduler_instance.add_job(
                send_daily_motivation,
                trigger=CronTrigger(hour=10, minute=0),
                kwargs={"bot": bot_instance, "db_manager": db_manager},
                id="daily_motivation",
                replace_existing=True,
            )
            scheduler_instance.start()
            logger.info("✅ Планировщик запущен (ежедневная мотивация в 10:00 МСК)")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска планировщика: {e}")
            # Не критично, продолжаем

        # --- Настройка обработчиков сигналов ---
        setup_signal_handlers()
        
        # --- Запуск бота ---
        logger.info("🚀 Запуск polling...")
        
        # Очищаем pending updates
        await bot_instance.delete_webhook(drop_pending_updates=True)
        
        # Запускаем polling
        await dp_instance.start_polling(
            bot_instance,
            allowed_updates=["message", "callback_query", "inline_query"],
            skip_updates=True,
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал прерывания (Ctrl+C)")
        await shutdown_handler("SIGINT")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        logger.exception("Полная информация об ошибке:")
        
        # Пытаемся graceful shutdown
        try:
            await shutdown_handler("ERROR")
        except:
            pass
        
        sys.exit(1)
    
    finally:
        # Финальная очистка
        if scheduler_instance:
            scheduler_instance.shutdown()
        if bot_instance:
            await bot_instance.session.close()
        
        logger.info("👋 Бот остановлен")


if __name__ == "__main__":
    try:
        # Проверяем конфигурацию перед запуском
        if not Config.TOKEN:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден!")
            print("Создайте .env файл и укажите BOT_TOKEN")
            sys.exit(1)
        
        if not Config.ADMIN_IDS:
            print("⚠️  ПРЕДУПРЕЖДЕНИЕ: ADMIN_IDS не указаны")
        
        # Запускаем бота
        asyncio.run(main())
        
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Бот остановлен пользователем")
        
    except Exception as e:
        print(f"❌ Критическая ошибка запуска: {e}")
        sys.exit(1)
