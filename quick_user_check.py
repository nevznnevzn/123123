"""
Быстрая проверка основных пользовательских функций с асинхронной БД
"""
import asyncio
import logging
from datetime import datetime
from services.ai_predictions import AIPredictionService
from services.star_advice_service import StarAdviceService
from services.motivation_service import MotivationService
from services.subscription_service import SubscriptionService
from services.antispam_service import AntiSpamService
from database_async import AsyncDatabaseManager
from models import PlanetPosition, Location

# Отключаем логи
logging.basicConfig(level=logging.ERROR)

async def quick_user_check():
    """Быстрая проверка всех основных функций"""
    print("🔍 БЫСТРАЯ ПРОВЕРКА ПОЛЬЗОВАТЕЛЬСКИХ ФУНКЦИЙ")
    print("=" * 50)
    
    # Инициализация БД
    db_manager = AsyncDatabaseManager("sqlite+aiosqlite:///quick_test.db")
    await db_manager.init_db()
    
    results = []
    
    # 1. Проверка регистрации пользователя
    print("\n👤 Проверка регистрации...")
    try:
        user, created = await db_manager.get_or_create_user(
            telegram_id=123456, name="Тест Пользователь"
        )
        if user:
            print("✅ Пользователь создан/получен")
            results.append(True)
        else:
            print("❌ Ошибка создания пользователя")
            results.append(False)
    except Exception as e:
        print(f"❌ Ошибка регистрации: {e}")
        results.append(False)
    
    # 2. Проверка обновления профиля
    print("\n📝 Проверка профиля...")
    try:
        updated_user = await db_manager.update_user_profile(
            telegram_id=123456,
            name="Тест Пользователь",
            gender="Мужской",
            birth_year=1990,
            birth_city="Москва",
            birth_date=datetime(1990, 7, 15, 12, 0),
            birth_time_specified=True
        )
        if updated_user and updated_user.is_profile_complete:
            print("✅ Профиль обновлен")
            results.append(True)
        else:
            print("❌ Ошибка обновления профиля")
            results.append(False)
    except Exception as e:
        print(f"❌ Ошибка профиля: {e}")
        results.append(False)
    
    # 3. Проверка создания натальной карты
    print("\n⭐ Проверка натальной карты...")
    try:
        test_planets = {
            "Солнце": {"sign": "Лев", "degree": 15.0},
            "Луна": {"sign": "Рак", "degree": 8.0},
            "Меркурий": {"sign": "Лев", "degree": 12.0},
        }
        
        chart = await db_manager.create_natal_chart(
            telegram_id=123456,
            name="Тест Пользователь",
            city="Москва",
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow",
            birth_date=datetime(1990, 7, 15, 12, 0),
            birth_time_specified=True,
            has_warning=False,
            planets_data=test_planets
        )
        if chart:
            print("✅ Натальная карта создана")
            results.append(True)
        else:
            print("❌ Ошибка создания карты")
            results.append(False)
    except Exception as e:
        print(f"❌ Ошибка карты: {e}")
        results.append(False)
    
    # 4. Проверка AI сервиса
    print("\n🤖 Проверка AI сервиса...")
    try:
        ai_service = AIPredictionService()
        if ai_service.client:
            print("✅ AI клиент инициализирован")
            results.append(True)
        else:
            print("❌ AI клиент не инициализирован")
            results.append(False)
    except Exception as e:
        print(f"❌ Ошибка AI: {e}")
        results.append(False)
    
    # 5. Проверка звездного совета
    print("\n🌟 Проверка звездного совета...")
    try:
        star_service = StarAdviceService()
        validation = await star_service.validate_question("Как мне найти работу?")
        if validation["is_valid"]:
            print("✅ Валидация вопросов работает")
            results.append(True)
        else:
            print("❌ Ошибка валидации")
            results.append(False)
    except Exception as e:
        print(f"❌ Ошибка звездного совета: {e}")
        results.append(False)
    
    # 6. Проверка мотиваций
    print("\n🌅 Проверка мотиваций...")
    try:
        motivation_service = MotivationService(AIPredictionService())
        print("✅ Сервис мотиваций создан")
        results.append(True)
    except Exception as e:
        print(f"❌ Ошибка мотиваций: {e}")
        results.append(False)
    
    # 7. Проверка подписки
    print("\n💎 Проверка подписки...")
    try:
        subscription_service = SubscriptionService()
        is_premium = subscription_service.is_user_premium(123456)
        print(f"✅ Система подписки работает: {'Premium' if is_premium else 'Free'}")
        results.append(True)
    except Exception as e:
        print(f"❌ Ошибка подписки: {e}")
        results.append(False)
    
    # 8. Проверка антиспама
    print("\n🛡️ Проверка антиспама...")
    try:
        antispam_service = AntiSpamService()
        limits = antispam_service.check_limits(123456, is_premium=False)
        print(f"✅ Антиспам работает: {limits['questions_left']} вопросов")
        results.append(True)
    except Exception as e:
        print(f"❌ Ошибка антиспама: {e}")
        results.append(False)
    
    # Итоги
    print("\n📊 РЕЗУЛЬТАТЫ:")
    print("-" * 20)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Работает: {passed}/{total}")
    print(f"❌ Проблемы: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ВСЕ ФУНКЦИИ РАБОТАЮТ!")
        print("✅ Бот готов к использованию")
        print("✅ Асинхронная БД функционирует")
        print("✅ Все сервисы активны")
    else:
        print("\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        print("❌ Требуется доработка")
    
    # Очистка
    await db_manager.delete_user_data(123456)
    await db_manager.close()
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(quick_user_check()) 