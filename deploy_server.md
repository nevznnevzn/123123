# 🚀 Развертывание SolarBalance на сервере (без Docker)

## 📋 Требования к серверу

### Минимальные требования:
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: 2GB минимум (рекомендуется 4GB)
- **CPU**: 1 ядро (рекомендуется 2 ядра)
- **Диск**: 10GB свободного места
- **Python**: 3.9+ (рекомендуется 3.11)

### Сетевые требования:
- Исходящие соединения к Telegram API
- Исходящие соединения к OpenAI/Bothub API
- Опционально: PostgreSQL сервер

## 🔧 Подготовка сервера

### 1. Обновление системы и установка зависимостей

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl wget
sudo apt install -y build-essential python3-dev
sudo apt install -y postgresql-client  # если используете PostgreSQL

# CentOS/RHEL
sudo yum update -y
sudo yum install -y python3 python3-pip python3-venv git curl wget
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python3-devel
```

### 2. Создание пользователя для бота

```bash
# Создаем отдельного пользователя для безопасности
sudo useradd -m -s /bin/bash solarbalance
sudo usermod -aG sudo solarbalance  # если нужны sudo права

# Переключаемся на пользователя
sudo su - solarbalance
```

## 📥 Установка проекта

### 1. Клонирование репозитория

```bash
cd /home/solarbalance
git clone <your-repository-url> solarbalance-bot
cd solarbalance-bot
```

### 2. Создание виртуального окружения

```bash
# Создаем venv
python3 -m venv venv

# Активируем venv
source venv/bin/activate

# Обновляем pip
pip install --upgrade pip
```

### 3. Установка зависимостей

```bash
# Устанавливаем основные зависимости
pip install -e .

# Или используем uv для ускорения (рекомендуется)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
uv pip install -e .
```

## ⚙️ Настройка конфигурации

### 1. Создание файла окружения

```bash
# Копируем пример конфигурации
cp env.example .env

# Редактируем конфигурацию
nano .env
```

### 2. Заполнение .env файла

```env
# Telegram Bot Configuration
BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER

# Database Configuration (SQLite для простоты)
DATABASE_URL=sqlite+aiosqlite:///solarbalance.db

# OpenAI API Configuration
AI_API=YOUR_BOTHUB_OR_OPENAI_API_KEY

# Admin Configuration (ваши Telegram ID)
ADMIN_IDS=123456789,987654321

# Environment
ENVIRONMENT=production

# Logging
LOG_LEVEL=INFO
LOG_FILE=/home/solarbalance/solarbalance-bot/logs/bot.log
```

### 3. Создание директорий для логов

```bash
mkdir -p logs
mkdir -p assets
chmod 755 logs assets
```

## 🗄️ Настройка базы данных

### Вариант 1: SQLite (простой)

```bash
# SQLite будет создана автоматически при первом запуске
# Убедитесь что путь в .env корректный:
DATABASE_URL=sqlite+aiosqlite:///$(pwd)/solarbalance.db
```

### Вариант 2: PostgreSQL (рекомендуется для продакшена)

```bash
# Установка PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Создание базы данных и пользователя
sudo -u postgres psql
```

```sql
CREATE DATABASE solarbalance;
CREATE USER solarbalance_user WITH ENCRYPTED PASSWORD 'secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE solarbalance TO solarbalance_user;
\q
```

```bash
# Обновите .env для PostgreSQL
DATABASE_URL=postgresql+asyncpg://solarbalance_user:secure_password_123@localhost:5432/solarbalance
```

## 🧪 Тестирование установки

### 1. Проверка зависимостей

```bash
source venv/bin/activate
python -c "import aiogram, swisseph, openai; print('Все зависимости установлены успешно')"
```

### 2. Тестовый запуск

```bash
# Активируем venv если не активен
source venv/bin/activate

# Тестовый запуск бота
python main_simple.py
```

### 3. Проверка логов

```bash
# Проверяем логи запуска
tail -f logs/bot.log

# Или смотрим прямой вывод
python main_simple.py
```

## 🔧 Настройка systemd сервиса

### 1. Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/solarbalance.service
```

```ini
[Unit]
Description=SolarBalance Astrology Telegram Bot
After=network.target postgresql.service
Wants=network.target

[Service]
Type=simple
User=solarbalance
Group=solarbalance
WorkingDirectory=/home/solarbalance/solarbalance-bot
Environment=PATH=/home/solarbalance/solarbalance-bot/venv/bin
ExecStart=/home/solarbalance/solarbalance-bot/venv/bin/python main_simple.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/solarbalance/solarbalance-bot

# Логи
StandardOutput=append:/home/solarbalance/solarbalance-bot/logs/systemd.log
StandardError=append:/home/solarbalance/solarbalance-bot/logs/systemd.log

[Install]
WantedBy=multi-user.target
```

### 2. Активация сервиса

```bash
# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable solarbalance

# Запускаем сервис
sudo systemctl start solarbalance

# Проверяем статус
sudo systemctl status solarbalance
```

## 📊 Мониторинг и управление

### Управление сервисом

```bash
# Запуск
sudo systemctl start solarbalance

# Остановка
sudo systemctl stop solarbalance

# Перезапуск
sudo systemctl restart solarbalance

# Статус
sudo systemctl status solarbalance

# Логи сервиса
sudo journalctl -u solarbalance -f
```

### Просмотр логов

```bash
# Логи приложения
tail -f /home/solarbalance/solarbalance-bot/logs/bot.log

# Логи systemd
sudo journalctl -u solarbalance -f

# Логи за последний час
sudo journalctl -u solarbalance --since "1 hour ago"
```

## 🔐 Безопасность

### 1. Настройка файрвола

```bash
# Устанавливаем ufw если не установлен
sudo apt install ufw

# Разрешаем SSH
sudo ufw allow ssh

# Разрешаем PostgreSQL если используете
sudo ufw allow 5432/tcp

# Включаем файрвол
sudo ufw enable
```

### 2. Права доступа

```bash
# Устанавливаем права на файлы
chmod 600 .env
chmod 755 *.py
chmod -R 755 handlers/ services/
chmod -R 766 logs/
```

### 3. Ротация логов

```bash
sudo nano /etc/logrotate.d/solarbalance
```

```
/home/solarbalance/solarbalance-bot/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 solarbalance solarbalance
    postrotate
        systemctl reload solarbalance
    endscript
}
```

## 🔄 Обновление проекта

### Скрипт для обновления

```bash
nano update_bot.sh
```

```bash
#!/bin/bash
set -e

echo "🔄 Обновление SolarBalance..."

# Останавливаем бота
sudo systemctl stop solarbalance

# Переходим в директорию проекта
cd /home/solarbalance/solarbalance-bot

# Активируем venv
source venv/bin/activate

# Получаем обновления
git pull origin main

# Обновляем зависимости
uv pip install -e .

# Проверяем миграции БД (если есть)
python -c "from database_async import async_db_manager; import asyncio; asyncio.run(async_db_manager.init_db())"

# Запускаем бота
sudo systemctl start solarbalance

echo "✅ Обновление завершено!"
echo "📊 Статус сервиса:"
sudo systemctl status solarbalance --no-pager
```

```bash
chmod +x update_bot.sh
```

## 📈 Мониторинг производительности

### 1. Создание скрипта мониторинга

```bash
nano monitor.sh
```

```bash
#!/bin/bash

echo "📊 SolarBalance Bot Status"
echo "========================="

# Статус сервиса
echo "🔧 Service Status:"
systemctl is-active solarbalance

# Использование ресурсов
echo -e "\n💻 Resource Usage:"
ps aux | grep python | grep solarbalance | awk '{print "CPU: " $3 "%, RAM: " $4 "%, PID: " $2}'

# Размер логов
echo -e "\n📝 Log Files:"
du -sh logs/

# Размер БД
echo -e "\n🗄️ Database:"
if [ -f "solarbalance.db" ]; then
    du -sh solarbalance.db
fi

# Последние ошибки
echo -e "\n❌ Recent Errors:"
journalctl -u solarbalance --since "1 hour ago" | grep -i error | tail -5
```

```bash
chmod +x monitor.sh
```

## 🆘 Устранение проблем

### Типичные проблемы и решения

1. **Ошибка "ModuleNotFoundError"**
   ```bash
   source venv/bin/activate
   pip install -e .
   ```

2. **Ошибка подключения к БД**
   ```bash
   # Проверьте .env файл
   cat .env | grep DATABASE_URL
   
   # Проверьте права доступа
   ls -la solarbalance.db
   ```

3. **Бот не отвечает**
   ```bash
   # Проверьте логи
   tail -f logs/bot.log
   
   # Проверьте токен
   cat .env | grep BOT_TOKEN
   ```

4. **Высокое потребление памяти**
   ```bash
   # Перезапустите сервис
   sudo systemctl restart solarbalance
   
   # Проверьте процессы
   ps aux | grep python
   ```

## ✅ Финальная проверка

После успешного развертывания проверьте:

- [ ] Бот отвечает на команду `/start`
- [ ] Админ-панель работает (`/admin`)
- [ ] Создание натальных карт функционирует
- [ ] Логи пишутся корректно
- [ ] Сервис автоматически запускается после перезагрузки

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `journalctl -u solarbalance -f`
2. Проверьте статус: `systemctl status solarbalance`
3. Проверьте конфигурацию: `cat .env`
4. Проверьте зависимости: `pip list`

Развертывание завершено! 🎉 