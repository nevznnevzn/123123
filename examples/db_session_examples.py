"""
Примеры использования декоратора @with_db_session и контекстного менеджера db_session_context
Демонстрирует применение принципа DRY для работы с сессиями БД
"""
import asyncio
from datetime import datetime
from database_async import AsyncDatabaseManager, with_db_session, db_session_context
from models import User, NatalChart
from sqlalchemy import select

# Инициализация БД
db_manager = AsyncDatabaseManager("sqlite+aiosqlite:///examples.db")


class UserService:
    """Сервис для работы с пользователями с применением декоратора @with_db_session"""
    
    def __init__(self, db_manager: AsyncDatabaseManager):
        self.db_manager = db_manager
    
    @with_db_session
    async def get_user_by_id(self, telegram_id: int) -> User:
        """Получить пользователя по ID - использует декоратор"""
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    @with_db_session
    async def create_user(self, telegram_id: int, name: str) -> User:
        """Создать пользователя - использует декоратор"""
        user = User(telegram_id=telegram_id, name=name)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user
    
    @with_db_session
    async def update_user_name(self, telegram_id: int, new_name: str) -> bool:
        """Обновить имя пользователя - использует декоратор"""
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        user.name = new_name
        await self._session.flush()
        return True
    
    @with_db_session
    async def get_user_charts(self, telegram_id: int) -> list[NatalChart]:
        """Получить натальные карты пользователя - использует декоратор"""
        result = await self._session.execute(
            select(NatalChart)
            .where(NatalChart.telegram_id == telegram_id)
            .order_by(NatalChart.created_at.desc())
        )
        return list(result.scalars().all())


class ChartService:
    """Сервис для работы с натальными картами с использованием контекстного менеджера"""
    
    def __init__(self, db_manager: AsyncDatabaseManager):
        self.db_manager = db_manager
    
    async def create_chart_with_context(self, telegram_id: int, name: str, city: str) -> NatalChart:
        """Создать натальную карту используя контекстный менеджер"""
        async with db_session_context(self.db_manager) as session:
            chart = NatalChart(
                telegram_id=telegram_id,
                name=name,
                city=city,
                latitude=55.7558,
                longitude=37.6176,
                timezone="Europe/Moscow",
                birth_date=datetime.now(),
                birth_time_specified=True,
                has_warning=False,
                planets_data={"Солнце": {"sign": "Лев", "degree": 15.0}}
            )
            
            session.add(chart)
            await session.flush()
            await session.refresh(chart)
            return chart
    
    async def get_charts_by_city(self, city: str) -> list[NatalChart]:
        """Получить все карты по городу используя контекстный менеджер"""
        async with db_session_context(self.db_manager) as session:
            result = await session.execute(
                select(NatalChart).where(NatalChart.city == city)
            )
            return list(result.scalars().all())


async def demonstrate_dry_principle():
    """Демонстрация применения принципа DRY"""
    print("🎯 ДЕМОНСТРАЦИЯ ПРИНЦИПА DRY В РАБОТЕ С БД")
    print("=" * 50)
    
    # Инициализация БД
    await db_manager.init_db()
    
    # Создание сервисов
    user_service = UserService(db_manager)
    chart_service = ChartService(db_manager)
    
    # Пример 1: Использование декоратора @with_db_session
    print("\n📝 ПРИМЕР 1: Декоратор @with_db_session")
    print("-" * 30)
    
    # Создание пользователя
    user = await user_service.create_user(123456, "Тест Пользователь")
    print(f"✅ Пользователь создан: {user.name}")
    
    # Получение пользователя
    found_user = await user_service.get_user_by_id(123456)
    print(f"✅ Пользователь найден: {found_user.name}")
    
    # Обновление пользователя
    success = await user_service.update_user_name(123456, "Обновленное Имя")
    print(f"✅ Имя обновлено: {success}")
    
    # Пример 2: Использование контекстного менеджера
    print("\n📝 ПРИМЕР 2: Контекстный менеджер db_session_context")
    print("-" * 30)
    
    # Создание натальной карты
    chart = await chart_service.create_chart_with_context(123456, "Моя карта", "Москва")
    print(f"✅ Натальная карта создана: {chart.name}")
    
    # Получение карт по городу
    charts = await chart_service.get_charts_by_city("Москва")
    print(f"✅ Найдено карт в Москве: {len(charts)}")
    
    # Пример 3: Сравнение с "грязным" кодом
    print("\n📝 ПРИМЕР 3: Сравнение с кодом без DRY")
    print("-" * 30)
    
    print("❌ БЕЗ DRY (повторяющийся код):")
    print("""
    async def get_user_bad(self, telegram_id: int):
        async with self.get_session() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            return result.scalar_one_or_none()
    
    async def create_user_bad(self, telegram_id: int, name: str):
        async with self.get_session() as session:
            user = User(telegram_id=telegram_id, name=name)
            session.add(user)
            await session.commit()
            return user
    """)
    
    print("✅ С DRY (декоратор):")
    print("""
    @with_db_session
    async def get_user_good(self, telegram_id: int):
        result = await self._session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()
    
    @with_db_session
    async def create_user_good(self, telegram_id: int, name: str):
        user = User(telegram_id=telegram_id, name=name)
        self._session.add(user)
        await self._session.flush()
        return user
    """)
    
    # Пример 4: Преимущества DRY
    print("\n📝 ПРИМЕР 4: Преимущества применения DRY")
    print("-" * 30)
    
    advantages = [
        "🚀 Меньше повторяющегося кода",
        "🔧 Централизованное управление сессиями",
        "🛡️ Автоматическая обработка ошибок и rollback",
        "📖 Более читаемый и понятный код",
        "⚡ Легче поддерживать и тестировать",
        "🎯 Единообразный подход к работе с БД"
    ]
    
    for advantage in advantages:
        print(advantage)
    
    # Очистка
    await db_manager.delete_user_data(123456)
    await db_manager.close()
    
    print("\n🎉 Демонстрация завершена!")


async def performance_comparison():
    """Сравнение производительности с и без DRY"""
    print("\n⚡ СРАВНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 40)
    
    await db_manager.init_db()
    user_service = UserService(db_manager)
    
    # Тест с декоратором
    start_time = asyncio.get_event_loop().time()
    
    for i in range(100):
        await user_service.create_user(1000 + i, f"User {i}")
    
    decorator_time = asyncio.get_event_loop().time() - start_time
    
    # Тест без декоратора (ручное управление сессиями)
    start_time = asyncio.get_event_loop().time()
    
    for i in range(100):
        async with db_manager.get_session() as session:
            user = User(telegram_id=2000 + i, name=f"User {i}")
            session.add(user)
            await session.flush()
    
    manual_time = asyncio.get_event_loop().time() - start_time
    
    print(f"⏱️ Время с декоратором: {decorator_time:.3f}с")
    print(f"⏱️ Время без декоратора: {manual_time:.3f}с")
    print(f"📈 Разница: {((manual_time - decorator_time) / manual_time * 100):.1f}%")
    
    # Очистка
    for i in range(100):
        await db_manager.delete_user_data(1000 + i)
        await db_manager.delete_user_data(2000 + i)
    
    await db_manager.close()


if __name__ == "__main__":
    async def main():
        await demonstrate_dry_principle()
        await performance_comparison()
    
    asyncio.run(main()) 