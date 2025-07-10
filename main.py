import asyncio
import logging
import sys

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


async def main():
    """Основная функция для запуска бота"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # --- Инициализация ---
    storage = MemoryStorage()
    db_manager = DatabaseManager("sqlite:///astro_bot.db")
    logger.info("✅ База данных инициализирована")

    bot = Bot(
        token=Config.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=storage, db_manager=db_manager, bot=bot)

    # --- Импорты ---
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

    # --- Сервисы ---
    astro_service = AstroService()
    subscription_service = SubscriptionService()

    # --- Регистрация роутеров ---
    admin_router = create_admin_router()
    auth_middleware = AdminAuthMiddleware(admin_ids=Config.ADMIN_IDS)
    admin_router.message.middleware(auth_middleware)
    admin_router.callback_query.middleware(auth_middleware)
    dp.include_router(admin_router)

    dp.include_router(
        create_profile_router(db_manager=db_manager, astro_service=astro_service)
    )
    dp.include_router(
        create_natal_chart_router(
            db_manager=db_manager,
            astro_service=astro_service,
            subscription_service=subscription_service,
        )
    )
    dp.include_router(predictions_router)
    dp.include_router(compatibility_router)
    dp.include_router(star_advice_router)
    dp.include_router(sky_map_router)
    dp.include_router(subscription_router)
    dp.include_router(common_router)
    logger.info("✅ Роутеры настроены")

    # --- Настройка команд и планировщика ---
    await set_bot_commands(bot)
    logger.info("✅ Команды бота установлены")

    scheduler = AsyncIOScheduler(timezone=timezone("Europe/Moscow"))
    scheduler.add_job(
        send_daily_motivation,
        trigger=CronTrigger(hour=10, minute=0),
        kwargs={"bot": bot, "db_manager": db_manager},
    )
    scheduler.start()
    logger.info("✅ Планировщик запущен. Задача на 10:00 МСК установлена.")

    # --- Запуск бота ---
    logger.info("🚀 Бот запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("❌ Бот остановлен")
