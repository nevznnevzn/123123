"""Быстрый тест AI с короткими таймаутами"""
import asyncio
import logging
from services.ai_predictions import AIPredictionService
from models import PlanetPosition

# Минимальное логирование
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test():
    print("🚀 Быстрый тест AI (8 сек таймаут)...")
    
    service = AIPredictionService()
    planets = {"Солнце": PlanetPosition(sign="Лев", degree=15.0)}
    
    print("🔮 Генерируем прогноз...")
    
    try:
        result = await asyncio.wait_for(
            service.generate_prediction(planets, "сегодня"),
            timeout=12  # Общий таймаут на весь процесс
        )
        
        print("\n✅ РЕЗУЛЬТАТ:")
        print("-" * 40)
        print(result[:200] + "..." if len(result) > 200 else result)
        print("-" * 40)
        
        if "✨ Создано с помощью астрологического ИИ" in result:
            print("🎉 AI РАБОТАЕТ!")
        else:
            print("⚠️ Fallback режим")
            
    except asyncio.TimeoutError:
        print("❌ Общий таймаут - AI слишком медленный")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test()) 