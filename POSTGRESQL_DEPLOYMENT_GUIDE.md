# 🗄️ Руководство по развертыванию с PostgreSQL

## 📋 Обзор

Это руководство поможет вам развернуть SolarBalance с PostgreSQL для продакшена. PostgreSQL обеспечивает:
- ✅ Высокую отказоустойчивость
- ✅ Лучшую производительность при больших нагрузках
- ✅ Поддержку конкурентных запросов
- ✅ ACID-совместимость
- ✅ Расширенные возможности SQL

## 🚀 Быстрый старт

### 1. Установка PostgreSQL

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### CentOS/RHEL:
```bash
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Windows:
1. Скачайте PostgreSQL с [официального сайта](https://www.postgresql.org/download/windows/)
2. Установите с настройками по умолчанию
3. Запомните пароль для пользователя `postgres`

### 2. Создание базы данных

```bash
# Подключаемся к PostgreSQL
sudo -u postgres psql

# Создаем пользователя и базу данных
CREATE USER solarbalance WITH PASSWORD 'your_secure_password';
CREATE DATABASE solarbalance OWNER solarbalance;
GRANT ALL PRIVILEGES ON DATABASE solarbalance TO solarbalance;
\q
```

### 3. Настройка переменных окружения

Создайте файл `.env`:

```bash
# === TELEGRAM BOT ===
BOT_TOKEN=your_telegram_bot_token_here

# === AI SERVICE ===
AI_API=your_bothub_api_key_here

# === DATABASE ===
DATABASE_URL=postgresql+asyncpg://solarbalance:your_secure_password@localhost:5432/solarbalance

# === ENVIRONMENT ===
ENVIRONMENT=production

# === POSTGRESQL CONFIGURATION ===
POSTGRESQL_POOL_SIZE=20
POSTGRESQL_MAX_OVERFLOW=30
POSTGRESQL_POOL_RECYCLE=3600
POSTGRESQL_ECHO=false
```

### 4. Установка зависимостей

```bash
# Установка с продакшен зависимостями
pip install -e .[prod]

# Или установка вручную
pip install asyncpg uvloop gunicorn
```

### 5. Инициализация базы данных

```bash
python -c "
import asyncio
from database_async import AsyncDatabaseManager

async def init():
    db = AsyncDatabaseManager()
    await db.init_db()
    await db.close()

asyncio.run(init())
"
```

## 🔄 Миграция с SQLite на PostgreSQL

### Автоматическая миграция

1. Убедитесь, что у вас есть резервная копия SQLite базы данных
2. Настройте переменные окружения:

```bash
export SQLITE_URL="sqlite+aiosqlite:///solarbalance.db"
export POSTGRESQL_URL="postgresql+asyncpg://solarbalance:password@localhost:5432/solarbalance"
```

3. Запустите миграцию:

```bash
python scripts/migrate_to_postgresql.py
```

### Ручная миграция

Если автоматическая миграция не подходит, используйте SQLAlchemy для экспорта/импорта:

```python
# Экспорт из SQLite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, NatalChart, Prediction

# SQLite
sqlite_engine = create_engine("sqlite:///solarbalance.db")
Session = sessionmaker(bind=sqlite_engine)
session = Session()

# Экспортируем данные
users = session.query(User).all()
charts = session.query(NatalChart).all()
predictions = session.query(Prediction).all()

# Импорт в PostgreSQL
postgresql_engine = create_engine("postgresql://solarbalance:password@localhost:5432/solarbalance")
PostgreSQLSession = sessionmaker(bind=postgresql_engine)
pg_session = PostgreSQLSession()

# Импортируем данные
for user in users:
    pg_session.add(user)
for chart in charts:
    pg_session.add(chart)
for prediction in predictions:
    pg_session.add(prediction)

pg_session.commit()
```

## ⚙️ Оптимизация PostgreSQL

### 1. Настройка postgresql.conf

```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```

Добавьте/измените следующие параметры:

```ini
# Память
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Соединения
max_connections = 100

# Логирование
log_statement = 'all'
log_duration = on
log_min_duration_statement = 1000

# Производительность
random_page_cost = 1.1
effective_io_concurrency = 200
```

### 2. Настройка pg_hba.conf

```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

Добавьте строку для локальных подключений:

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   solarbalance    solarbalance                            md5
host    solarbalance    solarbalance    127.0.0.1/32            md5
```

### 3. Перезапуск PostgreSQL

```bash
sudo systemctl restart postgresql
```

## 🔧 Мониторинг и обслуживание

### 1. Создание индексов

```sql
-- Индексы для улучшения производительности
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_natal_charts_telegram_id ON natal_charts(telegram_id);
CREATE INDEX idx_predictions_telegram_id ON predictions(telegram_id);
CREATE INDEX idx_subscriptions_telegram_id ON subscriptions(telegram_id);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_natal_charts_created_at ON natal_charts(created_at);
```

### 2. Мониторинг производительности

```sql
-- Активные соединения
SELECT count(*) FROM pg_stat_activity;

-- Медленные запросы
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Размер таблиц
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public';
```

### 3. Резервное копирование

```bash
# Создание резервной копии
pg_dump -U solarbalance -h localhost solarbalance > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из резервной копии
psql -U solarbalance -h localhost solarbalance < backup_20231201_120000.sql
```

## 🚀 Развертывание в облаке

### Railway

1. Создайте аккаунт на [Railway](https://railway.app/)
2. Создайте новый проект
3. Добавьте PostgreSQL сервис
4. Получите DATABASE_URL из переменных окружения
5. Настройте переменные окружения в вашем приложении

### Heroku

1. Установите Heroku CLI
2. Создайте приложение:
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
```

3. Получите DATABASE_URL:
```bash
heroku config:get DATABASE_URL
```

4. Разверните приложение:
```bash
git push heroku main
```

### DigitalOcean

1. Создайте Droplet с PostgreSQL
2. Настройте firewall
3. Создайте базу данных и пользователя
4. Настройте SSL соединения

## 🔒 Безопасность

### 1. Настройка SSL

```bash
# Генерация SSL сертификатов
sudo -u postgres openssl req -new -x509 -days 365 -nodes -text -out server.crt -keyout server.key -subj "/CN=db.yourdomain.com"

# Настройка postgresql.conf
ssl = on
ssl_cert_file = '/var/lib/postgresql/14/data/server.crt'
ssl_key_file = '/var/lib/postgresql/14/data/server.key'
```

### 2. Ограничение доступа

```bash
# Настройка firewall
sudo ufw allow from your_app_server_ip to any port 5432
sudo ufw deny 5432
```

### 3. Регулярные обновления

```bash
# Обновление PostgreSQL
sudo apt update
sudo apt upgrade postgresql postgresql-contrib
```

## 📊 Тестирование производительности

### 1. Тест подключений

```python
import asyncio
import time
from database_async import AsyncDatabaseManager

async def test_connections():
    db = AsyncDatabaseManager()
    await db.init_db()
    
    start_time = time.time()
    
    # Тестируем 100 одновременных подключений
    tasks = []
    for i in range(100):
        task = asyncio.create_task(test_query(db))
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    end_time = time.time()
    print(f"Время выполнения: {end_time - start_time:.2f} секунд")
    
    await db.close()

async def test_query(db):
    async with db.get_session() as session:
        result = await session.execute("SELECT 1")
        await result.fetchone()

asyncio.run(test_connections())
```

### 2. Тест нагрузки

```python
import asyncio
import aiohttp
import time

async def load_test():
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        tasks = []
        for i in range(50):
            task = asyncio.create_task(send_request(session))
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        success_count = sum(1 for r in responses if r == 200)
        
        print(f"Успешных запросов: {success_count}/{len(responses)}")
        print(f"Время выполнения: {end_time - start_time:.2f} секунд")

async def send_request(session):
    async with session.get('http://localhost:8000/health') as response:
        return response.status

asyncio.run(load_test())
```

## 🆘 Устранение неполадок

### Частые проблемы

1. **Ошибка подключения:**
   ```
   FATAL: password authentication failed
   ```
   **Решение:** Проверьте пароль и настройки pg_hba.conf

2. **Ошибка пула соединений:**
   ```
   QueuePool limit of size 20 overflow 30 reached
   ```
   **Решение:** Увеличьте POSTGRESQL_POOL_SIZE и POSTGRESQL_MAX_OVERFLOW

3. **Медленные запросы:**
   **Решение:** Создайте индексы и оптимизируйте запросы

4. **Нехватка памяти:**
   **Решение:** Увеличьте shared_buffers и work_mem

### Логи и диагностика

```bash
# Просмотр логов PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# Проверка статуса
sudo systemctl status postgresql

# Проверка подключений
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

## 📈 Метрики и мониторинг

### Ключевые метрики для отслеживания:

1. **Производительность:**
   - Время отклика запросов
   - Количество активных соединений
   - Размер пула соединений

2. **Надежность:**
   - Время безотказной работы
   - Количество ошибок подключения
   - Размер логов

3. **Масштабируемость:**
   - Количество одновременных пользователей
   - Использование CPU и памяти
   - Размер базы данных

## 🎯 Заключение

PostgreSQL обеспечивает надежную основу для продакшен-развертывания SolarBalance. Следуя этому руководству, вы получите:

- ✅ Высокую производительность
- ✅ Отказоустойчивость
- ✅ Масштабируемость
- ✅ Безопасность
- ✅ Простоту обслуживания

Для получения дополнительной помощи обращайтесь к документации PostgreSQL или создавайте issues в репозитории проекта. 