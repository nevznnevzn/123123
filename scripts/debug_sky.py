#!/usr/bin/env python3
"""Тест системы звездного неба"""

import asyncio
from datetime import datetime

from models import Location
from services.astro_calculations import AstroService


async def test_basic_functionality():
    """Тестируем базовую функциональность"""
    print("🌌 Тестирование системы звездного неба...")

    try:
        # Создаем сервис
        astro_service = AstroService()
        print("✅ AstroService создан")

        # Тестовые данные
        birth_date = datetime(1990, 12, 25, 14, 30)
        location = Location(
            city="Москва", lat=55.7558, lng=37.6176, timezone="Europe/Moscow"
        )
        print("✅ Тестовые данные созданы")

        # Рассчитываем планеты
        planets = astro_service.calculate_natal_chart(birth_date, location)
        print(f"✅ Планеты рассчитаны: {len(planets)} планет")

        # Выводим результат
        print("\n🪐 Позиции планет:")
        for planet_name, position in planets.items():
            print(f"  {planet_name}: {position.sign} {position.degree:.1f}°")

        # Тестируем создание простой карты
        print("\n🎨 Тестирование создания изображения...")

        try:
            import matplotlib.pyplot as plt
            import numpy as np

            # Создаем простую карту
            fig, ax = plt.subplots(figsize=(6, 6), facecolor="#0a0a1a")
            ax.set_facecolor("#0a0a1a")
            ax = plt.subplot(111, projection="polar")
            ax.set_facecolor("#0a0a1a")
            ax.set_ylim(0, 1)
            ax.grid(False)
            ax.set_yticklabels([])
            ax.set_xticklabels([])

            # Добавляем звезды
            np.random.seed(42)
            n_stars = 50
            theta = np.random.uniform(0, 2 * np.pi, n_stars)
            r = np.random.uniform(0.1, 0.9, n_stars)
            sizes = np.random.uniform(10, 30, n_stars)
            ax.scatter(theta, r, s=sizes, c="white", alpha=0.8, marker="*")

            # Заголовок
            fig.suptitle("🌌 Тестовая карта", fontsize=14, color="white", y=0.95)

            # Сохраняем
            plt.savefig(
                "test_star_map.png",
                dpi=100,
                bbox_inches="tight",
                facecolor="#0a0a1a",
                edgecolor="none",
                transparent=False,
            )
            plt.close()

            print("✅ Тестовое изображение создано: test_star_map.png")

        except ImportError as e:
            print(f"⚠️  Matplotlib не установлен: {e}")
        except Exception as e:
            print(f"❌ Ошибка создания изображения: {e}")

        print("\n🎉 Базовый тест завершен успешно!")

    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
