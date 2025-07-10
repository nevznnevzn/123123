"""
Тест AI прогнозов
"""
import asyncio
import logging
from datetime import datetime

from services.ai_predictions import AIPredictionService
from models import PlanetPosition

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

async def test_ai_predictions():
    """Тестирует AI прогнозы"""
    
    print("🧪 Тестирование AI прогнозов...")
    
    # Создаем сервис
    ai_service = AIPredictionService()
    
    # Тестовые планеты
    test_planets = {
        "Солнце": PlanetPosition(sign="Лев", degree=15.5),
        "Луна": PlanetPosition(sign="Скорпион", degree=22.3),
        "Меркурий": PlanetPosition(sign="Дева", degree=8.7),
        "Венера": PlanetPosition(sign="Рак", degree=28.1),
        "Марс": PlanetPosition(sign="Близнецы", degree=12.9)
    }
    
    # Тестируем разные типы прогнозов
    prediction_types = ["сегодня", "неделя", "месяц"]
    
    for pred_type in prediction_types:
        print(f"\n{'='*50}")
        print(f"🔮 Тестируем прогноз: {pred_type}")
        print('='*50)
        
        try:
            prediction = await ai_service.generate_prediction(
                user_planets=test_planets,
                prediction_type=pred_type,
                owner_name="Тестовый пользователь"
            )
            
            print(f"✅ Прогноз получен:")
            print(prediction)
            
            # Проверяем длину
            if len(prediction) > 100:
                print(f"📏 Длина прогноза: {len(prediction)} символов")
            else:
                print("⚠️ Прогноз слишком короткий")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print(f"\n{'='*50}")
    print("🏁 Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(test_ai_predictions()) 