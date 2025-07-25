"""
Скрипт миграции данных с SQLite на PostgreSQL
Используется для перехода с разработки на продакшен
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

import aiosqlite
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from models import Base, User, NatalChart, Prediction, Subscription, CompatibilityReport

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Мигратор данных между SQLite и PostgreSQL"""
    
    def __init__(self, sqlite_url: str, postgresql_url: str):
        self.sqlite_url = sqlite_url
        self.postgresql_url = postgresql_url
        
    async def migrate_all_data(self):
        """Миграция всех данных"""
        logger.info("🚀 Начинаем миграцию данных с SQLite на PostgreSQL")
        
        try:
            # Создаем таблицы в PostgreSQL
            await self.create_postgresql_tables()
            
            # Мигрируем данные
            await self.migrate_users()
            await self.migrate_natal_charts()
            await self.migrate_predictions()
            await self.migrate_subscriptions()
            await self.migrate_compatibility_reports()
            
            logger.info("✅ Миграция завершена успешно!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка миграции: {e}")
            raise
    
    async def create_postgresql_tables(self):
        """Создание таблиц в PostgreSQL"""
        logger.info("📋 Создание таблиц в PostgreSQL...")
        
        # Создаем engine для PostgreSQL
        engine = create_engine(self.postgresql_url.replace("+asyncpg", ""))
        
        # Создаем все таблицы
        Base.metadata.create_all(engine)
        engine.dispose()
        
        logger.info("✅ Таблицы созданы")
    
    async def migrate_users(self):
        """Миграция пользователей"""
        logger.info("👥 Миграция пользователей...")
        
        # Подключаемся к SQLite
        async with aiosqlite.connect(self.sqlite_url.replace("sqlite+aiosqlite:///", "")) as sqlite_conn:
            # Получаем всех пользователей
            async with sqlite_conn.execute("SELECT * FROM users") as cursor:
                users = await cursor.fetchall()
            
            # Получаем названия колонок
            columns = [description[0] for description in cursor.description]
            
            logger.info(f"📊 Найдено {len(users)} пользователей")
        
        # Подключаемся к PostgreSQL
        conn = await asyncpg.connect(self.postgresql_url.replace("+asyncpg", ""))
        
        try:
            for user_data in users:
                user_dict = dict(zip(columns, user_data))
                
                # Подготавливаем данные для вставки
                await conn.execute("""
                    INSERT INTO users (
                        telegram_id, name, gender, birth_year, birth_city,
                        birth_date, birth_time_specified, is_profile_complete,
                        notifications_enabled, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (telegram_id) DO NOTHING
                """, 
                    user_dict['telegram_id'],
                    user_dict['name'],
                    user_dict['gender'],
                    user_dict['birth_year'],
                    user_dict['birth_city'],
                    user_dict['birth_date'],
                    user_dict['birth_time_specified'],
                    user_dict['is_profile_complete'],
                    user_dict['notifications_enabled'],
                    user_dict['created_at']
                )
        
        finally:
            await conn.close()
        
        logger.info("✅ Пользователи мигрированы")
    
    async def migrate_natal_charts(self):
        """Миграция натальных карт"""
        logger.info("⭐ Миграция натальных карт...")
        
        # Подключаемся к SQLite
        async with aiosqlite.connect(self.sqlite_url.replace("sqlite+aiosqlite:///", "")) as sqlite_conn:
            async with sqlite_conn.execute("SELECT * FROM natal_charts") as cursor:
                charts = await cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            logger.info(f"📊 Найдено {len(charts)} натальных карт")
        
        # Подключаемся к PostgreSQL
        conn = await asyncpg.connect(self.postgresql_url.replace("+asyncpg", ""))
        
        try:
            for chart_data in charts:
                chart_dict = dict(zip(columns, chart_data))
                
                await conn.execute("""
                    INSERT INTO natal_charts (
                        telegram_id, name, chart_type, chart_owner_name,
                        city, latitude, longitude, timezone, birth_date,
                        birth_time_specified, has_warning, planets_data, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                    chart_dict['telegram_id'],
                    chart_dict['name'],
                    chart_dict['chart_type'],
                    chart_dict['chart_owner_name'],
                    chart_dict['city'],
                    chart_dict['latitude'],
                    chart_dict['longitude'],
                    chart_dict['timezone'],
                    chart_dict['birth_date'],
                    chart_dict['birth_time_specified'],
                    chart_dict['has_warning'],
                    chart_dict['planets_data'],
                    chart_dict['created_at']
                )
        
        finally:
            await conn.close()
        
        logger.info("✅ Натальные карты мигрированы")
    
    async def migrate_predictions(self):
        """Миграция прогнозов"""
        logger.info("🔮 Миграция прогнозов...")
        
        # Подключаемся к SQLite
        async with aiosqlite.connect(self.sqlite_url.replace("sqlite+aiosqlite:///", "")) as sqlite_conn:
            async with sqlite_conn.execute("SELECT * FROM predictions") as cursor:
                predictions = await cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            logger.info(f"📊 Найдено {len(predictions)} прогнозов")
        
        # Подключаемся к PostgreSQL
        conn = await asyncpg.connect(self.postgresql_url.replace("+asyncpg", ""))
        
        try:
            for pred_data in predictions:
                pred_dict = dict(zip(columns, pred_data))
                
                await conn.execute("""
                    INSERT INTO predictions (
                        telegram_id, chart_id, prediction_type, valid_from,
                        valid_until, content, generation_time, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    pred_dict['telegram_id'],
                    pred_dict['chart_id'],
                    pred_dict['prediction_type'],
                    pred_dict['valid_from'],
                    pred_dict['valid_until'],
                    pred_dict['content'],
                    pred_dict['generation_time'],
                    pred_dict['created_at']
                )
        
        finally:
            await conn.close()
        
        logger.info("✅ Прогнозы мигрированы")
    
    async def migrate_subscriptions(self):
        """Миграция подписок"""
        logger.info("💎 Миграция подписок...")
        
        # Подключаемся к SQLite
        async with aiosqlite.connect(self.sqlite_url.replace("sqlite+aiosqlite:///", "")) as sqlite_conn:
            async with sqlite_conn.execute("SELECT * FROM subscriptions") as cursor:
                subscriptions = await cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            logger.info(f"📊 Найдено {len(subscriptions)} подписок")
        
        # Подключаемся к PostgreSQL
        conn = await asyncpg.connect(self.postgresql_url.replace("+asyncpg", ""))
        
        try:
            for sub_data in subscriptions:
                sub_dict = dict(zip(columns, sub_data))
                
                await conn.execute("""
                    INSERT INTO subscriptions (
                        telegram_id, subscription_type, status, start_date,
                        end_date, payment_id, payment_amount, payment_currency,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                    sub_dict['telegram_id'],
                    sub_dict['subscription_type'],
                    sub_dict['status'],
                    sub_dict['start_date'],
                    sub_dict['end_date'],
                    sub_dict['payment_id'],
                    sub_dict['payment_amount'],
                    sub_dict['payment_currency'],
                    sub_dict['created_at'],
                    sub_dict['updated_at']
                )
        
        finally:
            await conn.close()
        
        logger.info("✅ Подписки мигрированы")
    
    async def migrate_compatibility_reports(self):
        """Миграция отчетов совместимости"""
        logger.info("💞 Миграция отчетов совместимости...")
        
        # Подключаемся к SQLite
        async with aiosqlite.connect(self.sqlite_url.replace("sqlite+aiosqlite:///", "")) as sqlite_conn:
            async with sqlite_conn.execute("SELECT * FROM compatibility_reports") as cursor:
                reports = await cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            logger.info(f"📊 Найдено {len(reports)} отчетов совместимости")
        
        # Подключаемся к PostgreSQL
        conn = await asyncpg.connect(self.postgresql_url.replace("+asyncpg", ""))
        
        try:
            for report_data in reports:
                report_dict = dict(zip(columns, report_data))
                
                await conn.execute("""
                    INSERT INTO compatibility_reports (
                        user_id, user_name, partner_name, user_birth_date,
                        partner_birth_date, sphere, report_text, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    report_dict['user_id'],
                    report_dict['user_name'],
                    report_dict['partner_name'],
                    report_dict['user_birth_date'],
                    report_dict['partner_birth_date'],
                    report_dict['sphere'],
                    report_dict['report_text'],
                    report_dict['created_at']
                )
        
        finally:
            await conn.close()
        
        logger.info("✅ Отчеты совместимости мигрированы")
    
    async def verify_migration(self):
        """Проверка успешности миграции"""
        logger.info("🔍 Проверка миграции...")
        
        # Подсчитываем записи в SQLite
        async with aiosqlite.connect(self.sqlite_url.replace("sqlite+aiosqlite:///", "")) as sqlite_conn:
            sqlite_counts = {}
            
            for table in ['users', 'natal_charts', 'predictions', 'subscriptions', 'compatibility_reports']:
                async with sqlite_conn.execute(f"SELECT COUNT(*) FROM {table}") as cursor:
                    count = await cursor.fetchone()
                    sqlite_counts[table] = count[0]
        
        # Подсчитываем записи в PostgreSQL
        conn = await asyncpg.connect(self.postgresql_url.replace("+asyncpg", ""))
        
        try:
            postgresql_counts = {}
            
            for table in ['users', 'natal_charts', 'predictions', 'subscriptions', 'compatibility_reports']:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                postgresql_counts[table] = count
            
            # Сравниваем результаты
            logger.info("📊 Результаты миграции:")
            logger.info("=" * 50)
            
            for table in sqlite_counts:
                sqlite_count = sqlite_counts[table]
                postgresql_count = postgresql_counts[table]
                
                status = "✅" if sqlite_count == postgresql_count else "❌"
                logger.info(f"{status} {table}: {sqlite_count} → {postgresql_count}")
            
            logger.info("=" * 50)
            
            # Проверяем общий успех
            all_match = all(sqlite_counts[table] == postgresql_counts[table] 
                          for table in sqlite_counts)
            
            if all_match:
                logger.info("🎉 Миграция прошла успешно!")
            else:
                logger.warning("⚠️ Обнаружены расхождения в данных")
        
        finally:
            await conn.close()


async def main():
    """Главная функция"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Получаем URL баз данных из переменных окружения
    sqlite_url = os.getenv("SQLITE_URL", "sqlite+aiosqlite:///solarbalance.db")
    postgresql_url = os.getenv("POSTGRESQL_URL")
    
    if not postgresql_url:
        logger.error("❌ POSTGRESQL_URL не указан в переменных окружения")
        return
    
    logger.info(f"📁 SQLite: {sqlite_url}")
    logger.info(f"🗄️ PostgreSQL: {postgresql_url}")
    
    # Создаем мигратор
    migrator = DatabaseMigrator(sqlite_url, postgresql_url)
    
    # Выполняем миграцию
    await migrator.migrate_all_data()
    
    # Проверяем результат
    await migrator.verify_migration()


if __name__ == "__main__":
    asyncio.run(main()) 