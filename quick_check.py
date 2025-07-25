"""
Быстрая проверка основных функций SolarBalance
"""
import asyncio
import logging
from datetime import datetime
from services.ai_predictions import AIPredictionService
from services.star_advice_service import StarAdviceService
from services.motivation_service import MotivationService
from services.subscription_service import SubscriptionService
from services.antispam_service import AntiSpamService
from models import PlanetPosition, Location

# Отключаем логи
logging.basicConfig(level=logging.ERROR)

async def quick_check():
    """Быстрая проверка всех сервисов"""
    print("🔍 БЫСТРАЯ ПРОВЕРКА SOLARBALANCE")
    print("=" * 40)
    
    results = []
    
    # 1. Проверка AI сервиса
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
    
    # 2. Проверка звездного совета
    print("\n🌟 Проверка звездного совета...")
    try:
        star_service = StarAdviceService()
        print("✅ Сервис звездного совета создан")
        results.append(True)
    except Exception as e:
        print(f"❌ Ошибка звездного совета: {e}")
        results.append(False)
    
    # 3. Проверка мотиваций
    print("\n🌅 Проверка мотиваций...")
    try:
        motivation_service = MotivationService(ai_service=ai_service)
        print("✅ Сервис мотиваций создан")
        results.append(True)
    except Exception as e:
        print(f"❌ Ошибка мотиваций: {e}")
        results.append(False)
    
    # 4. Проверка подписки
    print("\n💎 Проверка системы подписки...")
    try:
        subscription_service = SubscriptionService()
        print("✅ Сервис подписки создан")
        results.append(True)
    except Exception as e:
        print(f"❌ Ошибка подписки: {e}")
        results.append(False)
    
    # 5. Проверка антиспама
    print("\n🛡️ Проверка антиспама...")
    try:
        antispam_service = AntiSpamService()
        print("✅ Сервис антиспама создан")
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
        print("\n🎉 ВСЕ СЕРВИСЫ РАБОТАЮТ!")
        print("✅ Бот готов к использованию")
    else:
        print("\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        print("❌ Требуется доработка")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(quick_check()) 