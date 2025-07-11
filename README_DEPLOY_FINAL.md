# 🚀 SolarBalance - Готов к деплою на сервер!

## ✅ Что подготовлено

Бот **SolarBalance** полностью подготовлен к деплою на Linux сервер с использованием виртуального окружения Python (venv). Все необходимые файлы созданы и настроены.

### 📦 Файлы для деплоя:

- ✅ `deploy.sh` - Автоматический скрипт деплоя
- ✅ `start_server.sh` - Скрипт запуска бота
- ✅ `requirements-prod.txt` - Продакшен зависимости
- ✅ `env.example` - Пример переменных окружения
- ✅ `check_deploy.py` - Проверка готовности к деплою
- ✅ `DEPLOY_GUIDE.md` - Подробное руководство (400+ строк)
- ✅ `QUICK_DEPLOY_SUMMARY.md` - Краткое руководство
- ✅ Улучшенные `config.py` и `main.py` для продакшена

### 🔧 Улучшения для продакшена:

- ✅ **Продакшен-готовая конфигурация** с переменными окружения
- ✅ **Улучшенное логирование** с ротацией логов
- ✅ **Graceful shutdown** и обработка сигналов
- ✅ **Проверка переменных окружения** при запуске
- ✅ **Поддержка PostgreSQL** и SQLite
- ✅ **Systemd сервис** для автозапуска
- ✅ **Мониторинг и восстановление** после сбоев

## 🎯 Быстрый деплой (3 шага)

### 1. На сервере склонируйте проект:
```bash
git clone <your-repo-url> solarbalance
cd solarbalance
```

### 2. Запустите автоматический деплой:
```bash
chmod +x deploy.sh
./deploy.sh
```

### 3. Настройте переменные окружения:
```bash
nano .env
```
Укажите минимум:
```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321
AI_API=your_bothub_api_key
```

### 4. Запустите бота:
```bash
# Тестовый запуск
./start_server.sh

# Или как системный сервис
sudo systemctl start solarbalance
```

## 📋 Системные требования

- **ОС:** Ubuntu 18.04+, CentOS 7+, Debian 9+
- **Python:** 3.9+ (рекомендуется 3.10+)
- **RAM:** 1GB+ (рекомендуется 2GB+)
- **Диск:** 2GB+ свободного места
- **Сеть:** Доступ к интернету

## 🛠️ Что делает автоматический деплой

Скрипт `deploy.sh` автоматически:

1. ✅ Проверяет версию Python (3.9+)
2. ✅ Устанавливает системные зависимости
3. ✅ Создает виртуальное окружение
4. ✅ Устанавливает Python зависимости
5. ✅ Создает конфигурационные файлы
6. ✅ Создает необходимые директории
7. ✅ Настраивает systemd сервис
8. ✅ Проверяет корректность установки

## 🔍 Проверка готовности

Перед деплоем можно проверить готовность:
```bash
python check_deploy.py
```

Скрипт проверит:
- ✅ Версию Python
- ✅ Наличие всех файлов
- ✅ Импорты модулей
- ✅ Конфигурацию
- ✅ Переменные окружения
- ✅ Права доступа
- ✅ Безопасность

## 📂 Структура после деплоя

```
solarbalance/
├── venv/                    # Виртуальное окружение
├── logs/                    # Логи приложения
├── .env                     # Переменные окружения
├── astro_bot.db            # База данных SQLite
├── de421.bsp               # Файлы эфемерид Swiss Ephemeris
├── de422.bsp               # (скачиваются автоматически)
├── solarbalance.service    # Systemd сервис
├── deploy.sh               # Скрипт деплоя
├── start_server.sh         # Скрипт запуска
└── check_deploy.py         # Проверка готовности
```

## 🚨 Обязательные переменные окружения

В файле `.env` обязательно укажите:

```env
# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN=your_telegram_bot_token

# ID администраторов (через запятую)
ADMIN_IDS=123456789,987654321

# API ключ для AI прогнозов (Bothub)
AI_API=your_bothub_api_key
```

## 🔧 Управление сервисом

```bash
# Статус
sudo systemctl status solarbalance

# Запуск/остановка
sudo systemctl start solarbalance
sudo systemctl stop solarbalance
sudo systemctl restart solarbalance

# Автозапуск
sudo systemctl enable solarbalance
sudo systemctl disable solarbalance

# Логи
sudo journalctl -u solarbalance -f
sudo journalctl -u solarbalance -n 50
```

## 📊 Мониторинг

### Логи приложения:
```bash
# Логи в реальном времени
tail -f logs/bot.log

# Системные логи
sudo journalctl -u solarbalance -f
```

### Производительность:
```bash
# Использование ресурсов
top -p $(pgrep -f "python.*main.py")

# Статистика сервиса
systemctl show solarbalance --property=MainPID,ActiveState,SubState
```

## 🔒 Безопасность

### Автоматически настраивается:
- ✅ Права доступа к `.env` файлу (600)
- ✅ Исполняемые права на скрипты
- ✅ Запуск от непривилегированного пользователя
- ✅ Ограничения ресурсов в systemd

### Рекомендации:
- 🔐 Используйте сильные пароли
- 🛡️ Настройте файрвол
- 📦 Регулярно обновляйте систему
- 🔄 Настройте резервное копирование

## 🗄️ База данных

### SQLite (по умолчанию):
```env
DATABASE_URL=sqlite:///astro_bot.db
```

### PostgreSQL (рекомендуется для продакшена):
```env
DATABASE_URL=postgresql://user:password@localhost:5432/solarbalance
```

## 📈 Производительность

### Оптимизация:
- ✅ Асинхронная архитектура
- ✅ Пулы соединений
- ✅ Кэширование запросов
- ✅ Ограничения ресурсов
- ✅ Graceful shutdown

### Настройки systemd:
```ini
MemoryMax=1G        # Лимит памяти
CPUQuota=50%        # Лимит CPU
RestartSec=10       # Перезапуск через 10 сек
```

## 🚀 Дополнительные возможности

### Webhook режим:
```env
WEBHOOK_HOST=your-domain.com
WEBHOOK_PORT=8080
WEBHOOK_PATH=/webhook
```

### Redis кэширование:
```env
REDIS_URL=redis://localhost:6379/0
```

### Уведомления:
```env
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## 📞 Поддержка и устранение неполадок

### Частые проблемы:

1. **Бот не запускается**
   ```bash
   sudo journalctl -u solarbalance -n 50
   python check_deploy.py
   ```

2. **Ошибки зависимостей**
   ```bash
   source venv/bin/activate
   pip install -r requirements-prod.txt --force-reinstall
   ```

3. **Проблемы с базой данных**
   ```bash
   ls -la astro_bot.db
   python -c "from database import DatabaseManager; db = DatabaseManager()"
   ```

### Полезные команды:
```bash
# Проверка конфигурации
python -c "from config import Config; print('Config OK')"

# Проверка импортов
python -c "import aiogram, swisseph; print('Imports OK')"

# Тест подключения к Telegram
python -c "import asyncio; from aiogram import Bot; from config import Config; asyncio.run(Bot(Config.TOKEN).get_me())"
```

## 📚 Документация

- 📖 `DEPLOY_GUIDE.md` - Подробное руководство (400+ строк)
- 📋 `QUICK_DEPLOY_SUMMARY.md` - Краткое руководство
- 🔍 `check_deploy.py` - Автоматическая проверка
- 🚀 `deploy.sh` - Автоматический деплой
- ▶️ `start_server.sh` - Запуск бота

## ✅ Чек-лист деплоя

- [ ] Сервер подготовлен (Ubuntu/CentOS/Debian)
- [ ] Python 3.9+ установлен
- [ ] Проект скачан на сервер
- [ ] Запущен `./deploy.sh`
- [ ] Настроен `.env` файл
- [ ] Скачаны файлы эфемерид (автоматически)
- [ ] Проверена готовность: `python check_deploy.py`
- [ ] Бот запущен: `./start_server.sh`
- [ ] Настроен systemd сервис
- [ ] Проверены логи: `sudo journalctl -u solarbalance -f`

---

## 🎉 Готов к деплою!

SolarBalance полностью подготовлен к развертыванию на продакшен сервере. Все файлы созданы, скрипты готовы, документация написана.

**Следующий шаг:** Загрузите проект на сервер и запустите `./deploy.sh`

**Удачного деплоя! 🚀** 