#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Простой тест прогнозов без зависимостей"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_predictions import AIPredictionService
from models import PlanetPosition

async def test_predictions():
    """Тест генерации прогнозов"""
    print("🧪 ТЕСТИРОВАНИЕ ПРОГНОЗОВ")
    print("=" * 40)
    
    # Создаем сервис
    service = AIPredictionService()
    
    # Тестовые планеты
    test_planets = {
        'Солнце': PlanetPosition(sign='Лев', degree=15.5),
        'Луна': PlanetPosition(sign='Рак', degree=22.3),
    }
    
    # Тестируем разные типы прогнозов
    for pred_type in ['сегодня', 'неделя', 'месяц']:
        print(f"\n📅 Тестируем прогноз: {pred_type}")
        
        try:
            result = await service.generate_prediction(
                user_planets=test_planets,
                prediction_type=pred_type,
                owner_name="Тестовый пользователь"
            )
            
            if result and len(result) > 50:
                print(f"✅ Прогноз создан! Длина: {len(result)} символов")
                print(f"Начинается с: {result[:100]}...")
            else:
                print(f"❌ Короткий или пустой прогноз: {result}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print("\n🎯 Тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_predictions()) 