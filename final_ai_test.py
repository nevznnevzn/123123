"""Финальный тест AI прогнозов"""
import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ai_predictions import AIPredictionService
from models import PlanetPosition

async def test_ai():
    print("🔮 Тестируем AI прогнозы...")
    
    service = AIPredictionService()
    
    planets = {
        "Солнце": PlanetPosition(sign="Лев", degree=15.0),
        "Луна": PlanetPosition(sign="Скорпион", degree=22.0)
    }
    
    result = await service.generate_prediction(
        user_planets=planets,
        prediction_type="сегодня"
    )
    
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТ:")
    print("="*60)
    print(result)
    print("="*60)
    
    if "✨ Создано с помощью астрологического ИИ" in result:
        print("\n🎉 AI ПРОГНОЗЫ РАБОТАЮТ! ✅")
    else:
        print("\n⚠️ Используется fallback режим")

if __name__ == "__main__":
    try:
        asyncio.run(test_ai())
    except KeyboardInterrupt:
        print("\n❌ Тест прерван пользователем") 