"""
Быстрый тест AI прогноза
"""
import asyncio
import logging
from services.ai_predictions import AIPredictionService
from models import PlanetPosition

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

async def quick_test():
    print("🚀 Быстрый тест AI прогноза...")
    
    # Создаем сервис
    ai_service = AIPredictionService()
    
    # Простые тестовые планеты
    test_planets = {
        "Солнце": PlanetPosition(sign="Лев", degree=15.0),
        "Луна": PlanetPosition(sign="Скорпион", degree=22.0),
        "Меркурий": PlanetPosition(sign="Дева", degree=8.0)
    }
    
    try:
        print("🔮 Генерируем прогноз на сегодня...")
        prediction = await ai_service.generate_prediction(
            user_planets=test_planets,
            prediction_type="сегодня",
            owner_name="Тестовый пользователь"
        )
        
        print("✅ ПРОГНОЗ ПОЛУЧЕН:")
        print("-" * 50)
        print(prediction)
        print("-" * 50)
        print(f"📏 Длина: {len(prediction)} символов")
        
        # Проверяем на наличие AI маркера
        if "✨ Создано с помощью астрологического ИИ" in prediction:
            print("🤖 AI РАБОТАЕТ! ✅")
        else:
            print("⚠️ Используется fallback режим")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test()) 