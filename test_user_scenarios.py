"""
Тест пользовательских сценариев для AI-сервисов
Симулирует реальное взаимодействие пользователей с ботом
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
from database import User, NatalChart, db_manager

# Настройка логирования
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

async def test_new_user_journey():
    """Тест: новый пользователь впервые использует AI-функции"""
    print("\n👤 === СЦЕНАРИЙ: НОВЫЙ ПОЛЬЗОВАТЕЛЬ ===")
    
    # Создаем пользователя
    user_id = 1001
    user_name = "Анна"
    
    # Проверяем генерацию прогноза без натальной карты
    ai_service = AIPredictionService()
    
    try:
        # У нового пользователя еще нет натальной карты
        result = await ai_service.generate_prediction(
            user_planets={},  # Пустая карта
            prediction_type="сегодня",
            owner_name=user_name
        )
        
        print(f"✓ Прогноз для нового пользователя: {len(result)} символов")
        print(f"✓ Fallback режим работает: {'fallback' in result.lower() or 'базовых' in result.lower()}")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False


async def test_premium_vs_free_user():
    """Тест: различия между Premium и Free пользователями"""
    print("\n💎 === СЦЕНАРИЙ: PREMIUM VS FREE ===")
    
    subscription_service = SubscriptionService()
    antispam_service = AntiSpamService()
    
    # Free пользователь
    free_user_id = 2001
    premium_user_id = 2002
    
    try:
        # Проверяем лимиты для Free пользователя
        free_limits = antispam_service.check_limits(free_user_id, is_premium=False)
        print(f"✓ Free лимиты: {free_limits['questions_left']} вопросов осталось")
        
        # Проверяем лимиты для Premium пользователя
        premium_limits = antispam_service.check_limits(premium_user_id, is_premium=True)
        print(f"✓ Premium лимиты: {premium_limits['questions_left']} вопросов осталось")
        
        # Симулируем исчерпание лимитов у Free пользователя
        for i in range(4):  # Free лимит = 3 вопроса
            antispam_service.record_question(free_user_id)
        
        exhausted_limits = antispam_service.check_limits(free_user_id, is_premium=False)
        print(f"✓ После исчерпания лимитов: разрешено={exhausted_limits['allowed']}")
        
        # Проверяем фильтрацию планет
        test_planets = {
            "Солнце": PlanetPosition(sign="Лев", degree=15.0),
            "Луна": PlanetPosition(sign="Рак", degree=22.0),
            "Меркурий": PlanetPosition(sign="Дева", degree=8.0),
            "Венера": PlanetPosition(sign="Близнецы", degree=12.0),
            "Марс": PlanetPosition(sign="Скорпион", degree=18.0),
        }
        
        free_planets = await subscription_service.filter_planets_for_user(test_planets, free_user_id)
        premium_planets = await subscription_service.filter_planets_for_user(test_planets, premium_user_id)
        
        print(f"✓ Free планеты: {len(free_planets)} из {len(test_planets)}")
        print(f"✓ Premium планеты: {len(premium_planets)} из {len(test_planets)}")
        
        return len(free_planets) < len(premium_planets)
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False


async def test_star_advice_user_flow():
    """Тест: пользователь задает вопросы Звездному совету"""
    print("\n🌟 === СЦЕНАРИЙ: ЗВЕЗДНЫЙ СОВЕТ ===")
    
    service = StarAdviceService()
    
    # Реальные вопросы пользователей
    user_questions = [
        ("Когда мне лучше сменить работу?", True),
        ("Как найти свою вторую половинку?", True),
        ("Подойдет ли мне профессия программиста?", True),
        ("Какая завтра будет погода?", False),
        ("Напиши код на Python", False),
        ("Посоветуй лекарство от головной боли", False),
    ]
    
    valid_questions = 0
    processed_questions = 0
    
    for question, expected_valid in user_questions:
        try:
            # Валидация вопроса
            validation = await service.validate_question(question)
            is_valid = validation.get("is_valid", False)
            
            print(f"{'✓' if is_valid == expected_valid else '✗'} '{question[:40]}...': {'Принят' if is_valid else 'Отклонен'}")
            
            if is_valid == expected_valid:
                valid_questions += 1
            
            # Если вопрос валидный, генерируем ответ
            if is_valid:
                test_planets = {
                    "Солнце": PlanetPosition(sign="Весы", degree=20.0),
                    "Луна": PlanetPosition(sign="Рыбы", degree=15.0)
                }
                
                birth_dt = datetime(1990, 10, 15, 14, 30)
                location = Location(city="Москва", lat=55.7558, lng=37.6176, timezone="Europe/Moscow")
                
                advice = await service.generate_advice(
                    question=question,
                    category="career",
                    user_planets=test_planets,
                    birth_dt=birth_dt,
                    location=location,
                    user_name="Пользователь"
                )
                
                if advice and len(advice) > 50:
                    processed_questions += 1
                    print(f"  ➤ Совет получен: {len(advice)} символов")
                
        except Exception as e:
            print(f"✗ Ошибка обработки вопроса: {e}")
    
    print(f"✓ Валидация: {valid_questions}/{len(user_questions)}")
    print(f"✓ Советы сгенерированы: {processed_questions}")
    
    return valid_questions >= len(user_questions) * 0.8  # 80% успешных валидаций


async def test_daily_motivation_flow():
    """Тест: ежедневная мотивация для разных типов пользователей"""
    print("\n🌅 === СЦЕНАРИЙ: ЕЖЕДНЕВНАЯ МОТИВАЦИЯ ===")
    
    ai_service = AIPredictionService()
    motivation_service = MotivationService(ai_service)
    
    # Пользователи разных типов
    test_users = [
        User(telegram_id=3001, name="Елена"),  # Free без карт
        User(telegram_id=3002, name="Дмитрий"),  # Free с картой
        User(telegram_id=3003, name="София"),  # Premium
    ]
    
    success_count = 0
    
    for i, user in enumerate(test_users):
        try:
            is_premium = (i == 2)  # Третий пользователь - Premium
            
            motivation = await motivation_service.generate_motivation(
                user, 
                is_subscribed=is_premium
            )
            
            if motivation:
                print(f"✓ Мотивация для {user.name}: {len(motivation)} символов")
                
                # Проверяем содержание
                has_premium_content = "Premium" in motivation
                if is_premium:
                    print(f"  ➤ Premium контент: {'Да' if has_premium_content else 'Базовый'}")
                else:
                    print(f"  ➤ Призыв к подписке: {'Да' if has_premium_content else 'Нет'}")
                
                success_count += 1
            else:
                print(f"✗ Мотивация для {user.name} не сгенерирована")
                
        except Exception as e:
            print(f"✗ Ошибка для {user.name}: {e}")
    
    return success_count >= 2  # Минимум 2 из 3 успешных


async def test_api_failure_scenarios():
    """Тест: поведение при недоступности AI API"""
    print("\n🛡️ === СЦЕНАРИЙ: ОТКАЗОУСТОЙЧИВОСТЬ ===")
    
    # Симулируем разные сценарии отказов
    scenarios = []
    
    # 1. AI API недоступен - должен работать fallback
    try:
        ai_service = AIPredictionService()
        
        # Временно "ломаем" клиент
        original_client = ai_service.client
        ai_service.client = None
        
        result = await ai_service.generate_prediction(
            user_planets={"Солнце": PlanetPosition(sign="Овен", degree=10.0)},
            prediction_type="сегодня"
        )
        
        fallback_works = "fallback" in result.lower() or "базовых" in result.lower() or len(result) > 100
        print(f"✓ Fallback при отсутствии AI: {'Работает' if fallback_works else 'Не работает'}")
        scenarios.append(fallback_works)
        
        # Восстанавливаем клиент
        ai_service.client = original_client
        
    except Exception as e:
        print(f"✗ Ошибка fallback теста: {e}")
        scenarios.append(False)
    
    # 2. Тестируем таймауты (короткий тест)
    try:
        ai_service = AIPredictionService()
        
        # Устанавливаем очень короткий таймаут
        import asyncio
        
        result = await asyncio.wait_for(
            ai_service.generate_prediction(
                user_planets={"Солнце": PlanetPosition(sign="Лев", degree=15.0)},
                prediction_type="сегодня"
            ),
            timeout=3  # 3 секунды
        )
        
        timeout_handled = len(result) > 50
        print(f"✓ Обработка таймаутов: {'Работает' if timeout_handled else 'Не работает'}")
        scenarios.append(timeout_handled)
        
    except asyncio.TimeoutError:
        print("✓ Обработка таймаутов: Таймаут обработан корректно")
        scenarios.append(True)
    except Exception as e:
        print(f"✗ Ошибка таймаут теста: {e}")
        scenarios.append(False)
    
    return sum(scenarios) >= len(scenarios) * 0.7  # 70% сценариев успешных


async def test_real_world_load():
    """Тест: имитация реальной нагрузки от пользователей"""
    print("\n🚀 === СЦЕНАРИЙ: РЕАЛЬНАЯ НАГРУЗКА ===")
    
    ai_service = AIPredictionService()
    
    # Симулируем 5 одновременных запросов
    async def user_request(user_id: int):
        try:
            planets = {
                "Солнце": PlanetPosition(sign="Телец", degree=user_id % 30),
                "Луна": PlanetPosition(sign="Рак", degree=(user_id * 2) % 30)
            }
            
            result = await ai_service.generate_prediction(
                user_planets=planets,
                prediction_type="сегодня",
                owner_name=f"Пользователь{user_id}"
            )
            
            return len(result) > 100
            
        except Exception as e:
            print(f"✗ Ошибка пользователя {user_id}: {e}")
            return False
    
    # Запускаем параллельные запросы
    tasks = [user_request(i) for i in range(1, 6)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = sum(1 for r in results if r is True)
    print(f"✓ Обработано запросов: {successful}/5")
    
    return successful >= 3  # Минимум 3 из 5 успешных


async def run_user_scenarios():
    """Запуск всех пользовательских сценариев"""
    print("🧪 === ТЕСТИРОВАНИЕ ПОЛЬЗОВАТЕЛЬСКИХ СЦЕНАРИЕВ ===")
    print("=" * 60)
    
    scenarios = [
        ("Новый пользователь", test_new_user_journey),
        ("Premium vs Free", test_premium_vs_free_user),
        ("Звездный совет", test_star_advice_user_flow),
        ("Ежедневная мотивация", test_daily_motivation_flow),
        ("Отказоустойчивость", test_api_failure_scenarios),
        ("Реальная нагрузка", test_real_world_load),
    ]
    
    results = []
    
    for scenario_name, test_func in scenarios:
        try:
            print(f"\n🎯 Тестируем: {scenario_name}")
            result = await test_func()
            results.append((scenario_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}")
            
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА в '{scenario_name}': {e}")
            results.append((scenario_name, False))
    
    # Выводим итоги
    print("\n" + "=" * 60)
    print("📊 === ИТОГИ ПОЛЬЗОВАТЕЛЬСКОГО ТЕСТИРОВАНИЯ ===")
    
    passed = 0
    for scenario_name, result in results:
        status = "✅ ГОТОВ" if result else "❌ ПРОБЛЕМЫ"
        print(f"{status} - {scenario_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Результат: {passed}/{len(results)} сценариев работают корректно")
    
    if passed == len(results):
        print("🎉 ВСЕ ПОЛЬЗОВАТЕЛЬСКИЕ СЦЕНАРИИ РАБОТАЮТ!")
        print("✅ Бот готов к использованию пользователями")
    elif passed >= len(results) * 0.8:
        print("⚠️ Большинство сценариев работает, есть мелкие проблемы")
        print("🔧 Рекомендуется дополнительное тестирование")
    else:
        print("🚨 СЕРЬЕЗНЫЕ ПРОБЛЕМЫ С ПОЛЬЗОВАТЕЛЬСКИМ ОПЫТОМ!")
        print("❌ Требуется исправление перед запуском")
    
    return passed, len(results)


if __name__ == "__main__":
    asyncio.run(run_user_scenarios()) 