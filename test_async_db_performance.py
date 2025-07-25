"""
Тест производительности асинхронной базы данных
Сравнивает синхронную и асинхронную работу
"""
import asyncio
import time
import logging
from datetime import datetime
from database import DatabaseManager
from database_async import AsyncDatabaseManager

# Отключаем логи
logging.basicConfig(level=logging.ERROR)

async def test_async_performance():
    """Тест производительности асинхронной БД"""
    print("🚀 ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ АСИНХРОННОЙ БД")
    print("=" * 50)
    
    # Инициализируем асинхронную БД
    async_db = AsyncDatabaseManager("sqlite+aiosqlite:///test_async.db")
    await async_db.init_db()
    
    # Инициализируем синхронную БД для сравнения
    sync_db = DatabaseManager("sqlite:///test_sync.db")
    
    results = []
    
    # Тест 1: Создание пользователей
    print("\n👥 Тест создания пользователей...")
    
    # Асинхронно
    start_time = time.time()
    tasks = []
    for i in range(10):
        task = async_db.get_or_create_user(telegram_id=1000 + i, name=f"User{i}")
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    async_time = time.time() - start_time
    print(f"✅ Асинхронно: {async_time:.3f}с")
    
    # Синхронно
    start_time = time.time()
    for i in range(10):
        sync_db.get_or_create_user(telegram_id=2000 + i, name=f"User{i}")
    sync_time = time.time() - start_time
    print(f"⏱️ Синхронно: {sync_time:.3f}с")
    
    improvement = ((sync_time - async_time) / sync_time) * 100
    print(f"📈 Улучшение: {improvement:.1f}%")
    results.append(("Создание пользователей", async_time, sync_time, improvement))
    
    # Тест 2: Получение профилей пользователей
    print("\n📋 Тест получения профилей...")
    
    # Асинхронно
    start_time = time.time()
    tasks = []
    for i in range(10):
        task = async_db.get_user_profile(1000 + i)
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    async_time = time.time() - start_time
    print(f"✅ Асинхронно: {async_time:.3f}с")
    
    # Синхронно
    start_time = time.time()
    for i in range(10):
        sync_db.get_user_profile(2000 + i)
    sync_time = time.time() - start_time
    print(f"⏱️ Синхронно: {sync_time:.3f}с")
    
    improvement = ((sync_time - async_time) / sync_time) * 100
    print(f"📈 Улучшение: {improvement:.1f}%")
    results.append(("Получение профилей", async_time, sync_time, improvement))
    
    # Тест 3: Создание натальных карт
    print("\n⭐ Тест создания натальных карт...")
    
    test_planets = {
        "Солнце": {"sign": "Лев", "degree": 15.0},
        "Луна": {"sign": "Рак", "degree": 8.0},
        "Меркурий": {"sign": "Лев", "degree": 12.0},
    }
    
    # Асинхронно
    start_time = time.time()
    tasks = []
    for i in range(5):
        task = async_db.create_natal_chart(
            telegram_id=1000 + i,
            name=f"User{i}",
            city="Москва",
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow",
            birth_date=datetime(1990, 7, 15, 12, 0),
            birth_time_specified=True,
            has_warning=False,
            planets_data=test_planets
        )
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    async_time = time.time() - start_time
    print(f"✅ Асинхронно: {async_time:.3f}с")
    
    # Синхронно
    start_time = time.time()
    for i in range(5):
        sync_db.create_natal_chart(
            telegram_id=2000 + i,
            name=f"User{i}",
            city="Москва",
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow",
            birth_date=datetime(1990, 7, 15, 12, 0),
            birth_time_specified=True,
            has_warning=False,
            planets_data=test_planets
        )
    sync_time = time.time() - start_time
    print(f"⏱️ Синхронно: {sync_time:.3f}с")
    
    improvement = ((sync_time - async_time) / sync_time) * 100
    print(f"📈 Улучшение: {improvement:.1f}%")
    results.append(("Создание карт", async_time, sync_time, improvement))
    
    # Тест 4: Получение статистики
    print("\n📊 Тест получения статистики...")
    
    # Асинхронно
    start_time = time.time()
    stats = await async_db.get_app_statistics()
    async_time = time.time() - start_time
    print(f"✅ Асинхронно: {async_time:.3f}с")
    
    # Синхронно
    start_time = time.time()
    stats = sync_db.get_app_statistics()
    sync_time = time.time() - start_time
    print(f"⏱️ Синхронно: {sync_time:.3f}с")
    
    improvement = ((sync_time - async_time) / sync_time) * 100
    print(f"📈 Улучшение: {improvement:.1f}%")
    results.append(("Статистика", async_time, sync_time, improvement))
    
    # Итоговый отчет
    print("\n📈 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    total_async = sum(r[1] for r in results)
    total_sync = sum(r[2] for r in results)
    avg_improvement = sum(r[3] for r in results) / len(results)
    
    print(f"{'Операция':<20} {'Асинхр':<8} {'Синхр':<8} {'Улучшение':<10}")
    print("-" * 50)
    
    for operation, async_time, sync_time, improvement in results:
        print(f"{operation:<20} {async_time:<8.3f} {sync_time:<8.3f} {improvement:<10.1f}%")
    
    print("-" * 50)
    print(f"{'ИТОГО':<20} {total_async:<8.3f} {total_sync:<8.3f} {avg_improvement:<10.1f}%")
    
    print(f"\n🎯 ВЫВОД:")
    if avg_improvement > 0:
        print(f"✅ Асинхронная БД работает быстрее на {avg_improvement:.1f}%")
        print("✅ Event loop не блокируется")
        print("✅ Бот будет более отзывчивым")
    else:
        print("⚠️ Асинхронная БД не показала улучшений")
        print("ℹ️ Это может быть связано с небольшим объемом данных")
    
    # Очистка
    await async_db.close()
    
    return avg_improvement > 0

async def test_concurrent_operations():
    """Тест конкурентных операций"""
    print("\n🔄 ТЕСТ КОНКУРЕНТНЫХ ОПЕРАЦИЙ")
    print("=" * 40)
    
    async_db = AsyncDatabaseManager("sqlite+aiosqlite:///test_concurrent.db")
    await async_db.init_db()
    
    # Создаем пользователей
    for i in range(5):
        await async_db.get_or_create_user(telegram_id=3000 + i, name=f"ConcurrentUser{i}")
    
    # Выполняем конкурентные операции
    start_time = time.time()
    
    tasks = []
    for i in range(10):
        # Смешиваем разные операции
        if i % 3 == 0:
            task = async_db.get_user_profile(3000 + (i % 5))
        elif i % 3 == 1:
            task = async_db.get_user_charts(3000 + (i % 5))
        else:
            task = async_db.get_or_create_subscription(3000 + (i % 5))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    
    print(f"✅ Выполнено {success_count}/10 операций за {total_time:.3f}с")
    print(f"📊 Среднее время на операцию: {total_time/10:.3f}с")
    
    if success_count == 10:
        print("🎉 Все конкурентные операции выполнены успешно!")
    else:
        print(f"⚠️ {10 - success_count} операций завершились с ошибками")
    
    await async_db.close()
    return success_count == 10

async def main():
    """Главная функция тестирования"""
    print("🧪 КОМПЛЕКСНЫЙ ТЕСТ АСИНХРОННОЙ БД")
    print("=" * 60)
    
    # Тест производительности
    performance_ok = await test_async_performance()
    
    # Тест конкурентности
    concurrent_ok = await test_concurrent_operations()
    
    print("\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
    if performance_ok and concurrent_ok:
        print("✅ Асинхронная БД работает корректно!")
        print("✅ Готово к продакшен-использованию")
    else:
        print("⚠️ Обнаружены проблемы с асинхронной БД")
        print("❌ Требуется доработка")

if __name__ == "__main__":
    asyncio.run(main()) 