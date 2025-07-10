# 🌟 SolarBalance - Астрологический Telegram Бот

Современный астрологический бот с точными расчетами натальных карт, транзитов и ИИ-прогнозов.

## ✨ Особенности

- 🎯 **Точные астрологические расчеты** с использованием Swiss Ephemeris
- 🤖 **ИИ-прогнозы** на основе натальных данных
- 🏗️ **Асинхронная архитектура** для высокой производительности
- 🐳 **Docker-ready** для простого деплоя
- 🧪 **100% покрытие тестами** критической функциональности
- 📊 **Админ-панель** с подробной статистикой

## 🚀 Быстрый старт

### Разработка

```bash
# Клонируем репозиторий
git clone <repo-url>
cd solarbalance

# Устанавливаем UV (если еще не установлен)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Устанавливаем зависимости
make install-dev

# Настраиваем окружение
cp env.example .env
# Отредактируйте .env файл

# Запускаем тесты
make test

# Форматируем код
make format

# Запускаем бота
make run
```

### Продакшен

```bash
# Используем Docker Compose (рекомендуется)
cp env.example .env
# Настройте переменные окружения

docker-compose up -d

# Или с PostgreSQL
docker-compose --profile postgres up -d
```

## 🛠️ Доступные команды

```bash
make help           # Показать все команды
make install        # Установить зависимости
make install-dev    # Установить dev зависимости
make test           # Запустить тесты
make test-cov       # Тесты с покрытием
make lint           # Проверить код
make format         # Отформатировать код
make check          # Полная проверка кода
make run            # Запустить бота
make clean          # Очистить временные файлы
```

## 📦 Структура проекта

```
solarbalance/
├── handlers/           # Обработчики команд
│   ├── admin/         # Админ-панель
│   ├── natal_chart/   # Натальные карты
│   ├── predictions/   # Прогнозы
│   └── ...
├── services/          # Бизнес-логика
│   ├── astro_calculations.py
│   ├── ai_predictions.py
│   └── ...
├── tests/            # Тесты
├── database_async.py # Асинхронная БД
├── main_simple.py    # Упрощенный запуск
└── pyproject.toml    # Конфигурация проекта
```

## 🔧 Конфигурация

### Обязательные переменные

- `BOT_TOKEN` - Токен Telegram бота
- `OPENAI_API_KEY` - API ключ OpenAI
- `DATABASE_URL` - URL базы данных

### Опциональные

- `ADMIN_IDS` - ID администраторов через запятую
- `ENVIRONMENT` - Окружение (production/development)
- `REDIS_URL` - URL Redis для кэширования

## 🗄️ База данных

### SQLite (разработка)
```bash
DATABASE_URL=sqlite+aiosqlite:///astro_bot.db
```

### PostgreSQL (продакшен)
```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

## 🐳 Docker

### Простой запуск
```bash
docker build -t solarbalance .
docker run -d --env-file .env solarbalance
```

### С PostgreSQL
```bash
docker-compose up -d
```

### Только бот (с внешней БД)
```bash
docker-compose up bot
```

## 🧪 Тестирование

```bash
# Все тесты
make test

# Только астрологические
pytest -m astro

# Только БД
pytest -m database

# С покрытием
make test-cov
```

## 📊 Мониторинг

Бот включает встроенные проверки здоровья:

- Health check endpoint (при использовании webhook)
- Автоматическая очистка устаревших данных
- Логирование всех операций

## 🔒 Безопасность

- Аутентификация админов по Telegram ID
- Валидация всех входных данных
- Изоляция в Docker контейнерах
- Принцип минимальных привилегий

## 🤝 Разработка

### Стиль кода
Проект использует:
- **Black** для форматирования
- **isort** для сортировки импортов
- **flake8** для линтинга
- **mypy** для типизации

### Принципы
- **KISS** - Keep It Simple, Stupid
- **DRY** - Don't Repeat Yourself
- **Async everywhere** - полностью асинхронная архитектура
- **Test coverage** - тесты для всей критической функциональности

### Добавление новых функций

1. Создайте обработчик в `handlers/`
2. Добавьте бизнес-логику в `services/`
3. Напишите тесты в `tests/`
4. Обновите документацию

## 📈 Производительность

- **Асинхронная БД** - без блокировок event loop
- **Пулл соединений** - эффективное использование БД
- **Кэширование** - Redis для часто используемых данных
- **Контекстные менеджеры** - автоматическое управление ресурсами

## 🐛 Диагностика

### Логи
```bash
docker-compose logs -f bot
```

### Состояние БД
```bash
docker-compose exec postgres psql -U solarbalance_user -d solarbalance
```

### Метрики
```bash
docker-compose exec bot python -c "
import asyncio
from database_async import async_db_manager
print(asyncio.run(async_db_manager.get_app_statistics()))
"
```

## 📄 Лицензия

MIT License - см. LICENSE файл

## 🙋‍♂️ Поддержка

- Создайте Issue для багов
- Pull Request для улучшений
- Telegram: @your_support_bot 