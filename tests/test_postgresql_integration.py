"""
Тесты интеграции с PostgreSQL
Проверяет работу асинхронной базы данных с PostgreSQL
"""
import asyncio
import os
import pytest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

from database_async import AsyncDatabaseManager
from database import User, NatalChart, Prediction, Subscription


class TestPostgreSQLIntegration:
    """Тесты интеграции с PostgreSQL"""
    
    @pytest.fixture
    async def postgresql_db(self):
        """Фикстура для PostgreSQL базы данных"""
        # Используем тестовую PostgreSQL базу данных
        test_db_url = os.getenv("TEST_POSTGRESQL_URL", "postgresql+asyncpg://test:test@localhost:5432/solarbalance_test")
        
        db = AsyncDatabaseManager(test_db_url)
        await db.init_db()
        
        yield db
        
        await db.close()
    
    @pytest.mark.asyncio
    async def test_postgresql_connection(self, postgresql_db):
        """Тест подключения к PostgreSQL"""
        async with postgresql_db.get_session() as session:
            result = await session.execute("SELECT version()")
            version = await result.fetchone()
            
            assert version is not None
            assert "PostgreSQL" in str(version[0])
    
    @pytest.mark.asyncio
    async def test_user_operations_postgresql(self, postgresql_db):
        """Тест операций с пользователями в PostgreSQL"""
        async with postgresql_db.get_session() as session:
            # Создаем пользователя
            user = User(
                telegram_id=123456789,
                name="Test User",
                gender="М",
                birth_year=1990,
                birth_city="Москва",
                birth_date=datetime(1990, 1, 1),
                birth_time_specified=True,
                is_profile_complete=True,
                notifications_enabled=True
            )
            
            session.add(user)
            await session.commit()
            
            # Получаем пользователя
            result = await session.execute(
                "SELECT * FROM users WHERE telegram_id = :telegram_id",
                {"telegram_id": 123456789}
            )
            user_data = await result.fetchone()
            
            assert user_data is not None
            assert user_data.name == "Test User"
            assert user_data.gender == "М"
    
    @pytest.mark.asyncio
    async def test_natal_chart_operations_postgresql(self, postgresql_db):
        """Тест операций с натальными картами в PostgreSQL"""
        async with postgresql_db.get_session() as session:
            # Создаем натальную карту
            chart = NatalChart(
                telegram_id=123456789,
                name="Test Chart",
                chart_type="natal",
                chart_owner_name="Test Owner",
                city="Москва",
                latitude=55.7558,
                longitude=37.6176,
                timezone="Europe/Moscow",
                birth_date=datetime(1990, 1, 1, 12, 0),
                birth_time_specified=True,
                has_warning=False,
                planets_data='{"Sun": {"sign": "Козерог", "degree": 10.5}}'
            )
            
            session.add(chart)
            await session.commit()
            
            # Получаем натальную карту
            result = await session.execute(
                "SELECT * FROM natal_charts WHERE telegram_id = :telegram_id",
                {"telegram_id": 123456789}
            )
            chart_data = await result.fetchone()
            
            assert chart_data is not None
            assert chart_data.name == "Test Chart"
            assert chart_data.chart_type == "natal"
            assert chart_data.latitude == 55.7558
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_postgresql(self, postgresql_db):
        """Тест конкурентных операций в PostgreSQL"""
        async def create_user(user_id: int):
            async with postgresql_db.get_session() as session:
                user = User(
                    telegram_id=user_id,
                    name=f"User {user_id}",
                    gender="М",
                    birth_year=1990,
                    birth_city="Москва",
                    birth_date=datetime(1990, 1, 1),
                    birth_time_specified=True,
                    is_profile_complete=True,
                    notifications_enabled=True
                )
                
                session.add(user)
                await session.commit()
        
        # Создаем 10 пользователей одновременно
        tasks = [create_user(i) for i in range(1000, 1010)]
        await asyncio.gather(*tasks)
        
        # Проверяем, что все пользователи созданы
        async with postgresql_db.get_session() as session:
            result = await session.execute("SELECT COUNT(*) FROM users WHERE telegram_id >= 1000 AND telegram_id < 1010")
            count = await result.fetchone()
            
            assert count[0] == 10
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_postgresql(self, postgresql_db):
        """Тест отката транзакций в PostgreSQL"""
        async with postgresql_db.get_session() as session:
            try:
                # Создаем пользователя
                user = User(
                    telegram_id=999999,
                    name="Rollback User",
                    gender="М",
                    birth_year=1990,
                    birth_city="Москва",
                    birth_date=datetime(1990, 1, 1),
                    birth_time_specified=True,
                    is_profile_complete=True,
                    notifications_enabled=True
                )
                
                session.add(user)
                await session.commit()
                
                # Проверяем, что пользователь создан
                result = await session.execute(
                    "SELECT * FROM users WHERE telegram_id = :telegram_id",
                    {"telegram_id": 999999}
                )
                user_data = await result.fetchone()
                assert user_data is not None
                
                # Имитируем ошибку и откат
                raise Exception("Test rollback")
                
            except Exception:
                await session.rollback()
                
                # Проверяем, что пользователь не был создан
                result = await session.execute(
                    "SELECT * FROM users WHERE telegram_id = :telegram_id",
                    {"telegram_id": 999999}
                )
                user_data = await result.fetchone()
                assert user_data is None
    
    @pytest.mark.asyncio
    async def test_json_operations_postgresql(self, postgresql_db):
        """Тест работы с JSON данными в PostgreSQL"""
        async with postgresql_db.get_session() as session:
            # Создаем натальную карту с JSON данными
            planets_data = {
                "Sun": {"sign": "Козерог", "degree": 10.5, "house": 1},
                "Moon": {"sign": "Рак", "degree": 25.3, "house": 7},
                "Mercury": {"sign": "Козерог", "degree": 5.2, "house": 1}
            }
            
            chart = NatalChart(
                telegram_id=888888,
                name="JSON Test Chart",
                chart_type="natal",
                chart_owner_name="JSON Test Owner",
                city="Москва",
                latitude=55.7558,
                longitude=37.6176,
                timezone="Europe/Moscow",
                birth_date=datetime(1990, 1, 1, 12, 0),
                birth_time_specified=True,
                has_warning=False,
                planets_data=str(planets_data)
            )
            
            session.add(chart)
            await session.commit()
            
            # Получаем и проверяем JSON данные
            result = await session.execute(
                "SELECT planets_data FROM natal_charts WHERE telegram_id = :telegram_id",
                {"telegram_id": 888888}
            )
            chart_data = await result.fetchone()
            
            assert chart_data is not None
            assert "Sun" in chart_data.planets_data
            assert "Козерог" in chart_data.planets_data
    
    @pytest.mark.asyncio
    async def test_index_performance_postgresql(self, postgresql_db):
        """Тест производительности индексов в PostgreSQL"""
        async with postgresql_db.get_session() as session:
            # Создаем индексы
            await session.execute("CREATE INDEX IF NOT EXISTS idx_test_users_telegram_id ON users(telegram_id)")
            await session.execute("CREATE INDEX IF NOT EXISTS idx_test_users_created_at ON users(created_at)")
            await session.commit()
            
            # Создаем тестовые данные
            for i in range(100):
                user = User(
                    telegram_id=2000 + i,
                    name=f"Performance User {i}",
                    gender="М",
                    birth_year=1990,
                    birth_city="Москва",
                    birth_date=datetime(1990, 1, 1),
                    birth_time_specified=True,
                    is_profile_complete=True,
                    notifications_enabled=True
                )
                session.add(user)
            
            await session.commit()
            
            # Тестируем запрос с индексом
            start_time = asyncio.get_event_loop().time()
            
            result = await session.execute(
                "SELECT * FROM users WHERE telegram_id = :telegram_id",
                {"telegram_id": 2050}
            )
            user_data = await result.fetchone()
            
            end_time = asyncio.get_event_loop().time()
            query_time = end_time - start_time
            
            assert user_data is not None
            assert query_time < 0.1  # Запрос должен выполняться быстро
    
    @pytest.mark.asyncio
    async def test_connection_pool_postgresql(self, postgresql_db):
        """Тест пула соединений PostgreSQL"""
        async def test_query():
            async with postgresql_db.get_session() as session:
                result = await session.execute("SELECT 1")
                return await result.fetchone()
        
        # Выполняем множество запросов одновременно
        tasks = [test_query() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        # Проверяем, что все запросы выполнились успешно
        assert len(results) == 50
        assert all(result is not None for result in results)
    
    @pytest.mark.asyncio
    async def test_data_types_postgresql(self, postgresql_db):
        """Тест различных типов данных в PostgreSQL"""
        async with postgresql_db.get_session() as session:
            # Тестируем различные типы данных
            user = User(
                telegram_id=777777,
                name="Data Types User",
                gender="Ж",
                birth_year=1985,
                birth_city="Санкт-Петербург",
                birth_date=datetime(1985, 6, 15, 14, 30, 45),
                birth_time_specified=True,
                is_profile_complete=False,
                notifications_enabled=True
            )
            
            session.add(user)
            await session.commit()
            
            # Проверяем сохранение данных
            result = await session.execute(
                "SELECT * FROM users WHERE telegram_id = :telegram_id",
                {"telegram_id": 777777}
            )
            user_data = await result.fetchone()
            
            assert user_data is not None
            assert user_data.name == "Data Types User"
            assert user_data.gender == "Ж"
            assert user_data.birth_year == 1985
            assert user_data.birth_city == "Санкт-Петербург"
            assert user_data.birth_date == datetime(1985, 6, 15, 14, 30, 45)
            assert user_data.is_profile_complete is False
            assert user_data.notifications_enabled is True


class TestPostgreSQLMigration:
    """Тесты миграции данных"""
    
    @pytest.mark.asyncio
    async def test_migration_script_structure(self):
        """Тест структуры скрипта миграции"""
        # Проверяем, что скрипт миграции существует
        migration_script = "scripts/migrate_to_postgresql.py"
        assert os.path.exists(migration_script)
        
        # Проверяем, что скрипт можно импортировать
        import importlib.util
        spec = importlib.util.spec_from_file_location("migrate", migration_script)
        module = importlib.util.module_from_spec(spec)
        
        # Проверяем наличие основных классов и функций
        assert hasattr(module, 'DatabaseMigrator')
        assert hasattr(module.DatabaseMigrator, 'migrate_all_data')
        assert hasattr(module.DatabaseMigrator, 'verify_migration')


class TestPostgreSQLConfiguration:
    """Тесты конфигурации PostgreSQL"""
    
    def test_postgresql_config_detection(self):
        """Тест определения конфигурации PostgreSQL"""
        from config import Config
        
        # Тестируем с PostgreSQL URL
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql+asyncpg://user:pass@localhost:5432/db'
        }):
            reload(Config)
            assert Config.IS_POSTGRESQL is True
            assert Config.IS_SQLITE is False
        
        # Тестируем с SQLite URL
        with patch.dict(os.environ, {
            'DATABASE_URL': 'sqlite+aiosqlite:///test.db'
        }):
            reload(Config)
            assert Config.IS_POSTGRESQL is False
            assert Config.IS_SQLITE is True
    
    def test_postgresql_pool_config(self):
        """Тест конфигурации пула PostgreSQL"""
        from config import Config
        
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql+asyncpg://user:pass@localhost:5432/db',
            'POSTGRESQL_POOL_SIZE': '50',
            'POSTGRESQL_MAX_OVERFLOW': '100'
        }):
            reload(Config)
            
            config = Config.get_database_config()
            assert config['pool_size'] == 50
            assert config['max_overflow'] == 100
            assert config['pool_pre_ping'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 