"""
Комплексная проверка всех AI-сервисов SolarBalance
"""
import asyncio
import logging
from datetime import datetime
from services.ai_predictions import AIPredictionService
from services.star_advice_service import StarAdviceService
from services.motivation_service import MotivationService
from models import PlanetPosition, Location, BirthData
from database import User, db_manager

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_ai_prediction_service():
    """Тест основного AI сервиса прогнозов"""
    print("\n🔮 === ТЕСТ AI PREDICTION SERVICE ===")
    
    service = AIPredictionService()
    
    # Проверяем инициализацию
    print(f"✓ AI клиент создан: {'Да' if service.client else 'Нет'}")
    
    # Тестируем генерацию прогноза
    test_planets = {
        "Солнце": PlanetPosition(sign="Лев", degree=15.5),
        "Луна": PlanetPosition(sign="Скорпион", degree=22.3),
        "Меркурий": PlanetPosition(sign="Дева", degree=8.7)
    }
    
    try:
        result = await service.generate_prediction(
            user_planets=test_planets,
            prediction_type="сегодня",
            owner_name="Тест"
        )
        
        print(f"✓ Прогноз сгенерирован: {len(result)} символов")
        print(f"✓ Содержит AI метку: {'AI' in result}")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False


async def test_star_advice_service():
    """Тест сервиса звездного совета"""
    print("\n🌟 === ТЕСТ STAR ADVICE SERVICE ===")
    
    service = StarAdviceService()
    
    # Проверяем валидацию вопросов
    test_questions = [
        ("Как мне найти любовь?", True),  # Валидный астрологический вопрос
        ("Какая погода завтра?", False),  # Невалидный вопрос
        ("Что говорят звезды о моей карьере?", True),  # Валидный вопрос
    ]
    
    validation_passed = 0
    for question, expected in test_questions:
        try:
            result = await service.validate_question(question)
            is_valid = result.get("is_valid", False)
            
            if is_valid == expected:
                print(f"✓ Валидация '{question[:30]}...': {is_valid}")
                validation_passed += 1
            else:
                print(f"✗ Валидация '{question[:30]}...': {is_valid} (ожидалось {expected})")
                
        except Exception as e:
            print(f"✗ Ошибка валидации: {e}")
    
    print(f"✓ Валидация пройдена: {validation_passed}/{len(test_questions)}")
    
    # Тест генерации ответа (если валидация работает)
    if validation_passed > 0:
        try:
            # Мокаем данные пользователя
            test_planets = {
                "Солнце": PlanetPosition(sign="Близнецы", degree=10.0),
                "Луна": PlanetPosition(sign="Дева", degree=25.0)
            }
            
            birth_dt = datetime(1990, 6, 15, 12, 0)
            location = Location(city="Москва", lat=55.7558, lng=37.6176, timezone="Europe/Moscow")
            
            # Используем простой вопрос
            answer = await service.generate_advice(
                question="Как мне найти свое предназначение?",
                category="growth",
                user_planets=test_planets,
                birth_dt=birth_dt,
                location=location,
                user_name="Тест"
            )
            
            print(f"✓ Совет сгенерирован: {len(answer)} символов")
            return True
            
        except Exception as e:
            print(f"✗ Ошибка генерации совета: {e}")
            return False
    
    return validation_passed > 0


async def test_motivation_service():
    """Тест сервиса мотиваций"""
    print("\n🌅 === ТЕСТ MOTIVATION SERVICE ===")
    
    ai_service = AIPredictionService()
    service = MotivationService(ai_service)
    
    # Создаем тестового пользователя
    test_user = User(
        telegram_id=999999999,
        name="Тестовый Пользователь"
    )
    
    try:
        motivation = await service.generate_motivation(test_user, is_subscribed=False)
        
        if motivation:
            print(f"✓ Мотивация сгенерирована: {len(motivation)} символов")
            print(f"✓ Содержит призыв к подписке: {'Premium' in motivation}")
            return True
        else:
            print("✗ Мотивация не сгенерирована")
            return False
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False


async def test_ai_fallback():
    """Тест fallback системы при недоступности AI"""
    print("\n🛡️ === ТЕСТ FALLBACK СИСТЕМЫ ===")
    
    # Создаем сервис с недействительным ключом
    import os
    original_key = os.environ.get('AI_API')
    os.environ['AI_API'] = 'invalid_key'
    
    try:
        # Пересоздаем сервис с невалидным ключом
        from importlib import reload
        import services.ai_predictions
        reload(services.ai_predictions)
        
        service = services.ai_predictions.AIPredictionService()
        
        test_planets = {
            "Солнце": PlanetPosition(sign="Овен", degree=10.0)
        }
        
        result = await service.generate_prediction(
            user_planets=test_planets,
            prediction_type="сегодня"
        )
        
        print(f"✓ Fallback прогноз получен: {len(result)} символов")
        print(f"✓ Это fallback: {'fallback' in result.lower() or 'базовых' in result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка fallback: {e}")
        return False
        
    finally:
        # Восстанавливаем оригинальный ключ
        if original_key:
            os.environ['AI_API'] = original_key
        elif 'AI_API' in os.environ:
            del os.environ['AI_API']


async def run_comprehensive_test():
    """Запуск всех тестов"""
    print("🧪 === КОМПЛЕКСНАЯ ПРОВЕРКА AI-СЕРВИСОВ ===")
    print("=" * 50)
    
    results = []
    
    # Запускаем все тесты
    tests = [
        ("AI Predictions", test_ai_prediction_service),
        ("Star Advice", test_star_advice_service),
        ("Motivation Service", test_motivation_service),
        ("Fallback System", test_ai_fallback),
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА в {test_name}: {e}")
            results.append((test_name, False))
    
    # Выводим итоги
    print("\n" + "=" * 50)
    print("📊 === ИТОГИ ТЕСТИРОВАНИЯ ===")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Результат: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("🎉 ВСЕ AI-СЕРВИСЫ РАБОТАЮТ КОРРЕКТНО!")
    elif passed > len(results) // 2:
        print("⚠️ Большинство сервисов работает, есть проблемы")
    else:
        print("🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ С AI-СЕРВИСАМИ!")
    
    return passed, len(results)


if __name__ == "__main__":
    asyncio.run(run_comprehensive_test()) 