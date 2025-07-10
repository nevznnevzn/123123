#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Быстрый тест fallback прогнозов"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_predictions import AIPredictionService

def test_fallback():
    """Тестируем fallback прогнозы"""
    print("🧪 ТЕСТ FALLBACK ПРОГНОЗОВ")
    print("=" * 40)
    
    service = AIPredictionService()
    
    # Тестируем прогнозы
    for pred_type in ['сегодня', 'неделя', 'месяц']:
        print(f"\n📅 Тестируем: {pred_type}")
        
        try:
            result = service._generate_fallback_prediction(pred_type, "Тест")
            if result and len(result) > 100:
                print(f"✅ Прогноз создан! Длина: {len(result)} символов")
                print(f"Начинается с: {result[:80]}...")
            else:
                print(f"❌ Проблема с прогнозом: {result}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print("\n🎯 Тест завершен!")

if __name__ == "__main__":
    test_fallback() 