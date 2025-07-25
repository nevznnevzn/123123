#!/bin/bash

# 🚀 Быстрый деплой Solar Balance Bot
# Использование: sudo bash quick_deploy.sh

set -e

echo "🚀 Быстрый деплой Solar Balance Bot"
echo "==================================="

# Проверка root прав
if [[ $EUID -ne 0 ]]; then
    echo "❌ Этот скрипт должен быть запущен с правами root (sudo)"
    exit 1
fi

# Обновление системы
echo "📦 Обновление системы..."
apt update && apt upgrade -y

# Установка зависимостей
echo "🔧 Установка зависимостей..."
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip git curl wget build-essential

# Создание пользователя
echo "👤 Создание пользователя..."
if ! id "solarbot" &>/dev/null; then
    useradd -m -s /bin/bash solarbot
    usermod -aG sudo solarbot
fi

# Копирование проекта
echo "📁 Копирование проекта..."
if [[ -f "main.py" ]]; then
    cp -r . /home/solarbot/solarbalance
    chown -R solarbot:solarbot /home/solarbot/solarbalance
else
    echo "❌ Файл main.py не найден в текущей директории"
    exit 1
fi

# Настройка venv
echo "🐍 Настройка виртуального окружения..."
su - solarbot -c "cd /home/solarbot/solarbalance && python3.11 -m venv venv"
su - solarbot -c "cd /home/solarbot/solarbalance && source venv/bin/activate && pip install --upgrade pip"

# Установка зависимостей
if [[ -f "/home/solarbot/solarbalance/requirements-prod.txt" ]]; then
    su - solarbot -c "cd /home/solarbot/solarbalance && source venv/bin/activate && pip install -r requirements-prod.txt"
else
    su - solarbot -c "cd /home/solarbot/solarbalance && source venv/bin/activate && pip install aiogram apscheduler pytz sqlalchemy asyncpg aiosqlite openai python-dotenv pyswisseph"
fi

# Создание .env
echo "⚙️ Создание конфигурации..."
if [[ ! -f "/home/solarbot/solarbalance/.env" ]]; then
    cat > /home/solarbot/solarbalance/.env << EOF
# Telegram Bot Token
BOT_TOKEN=your_bot_token_here

# Database (SQLite по умолчанию)
DATABASE_URL=sqlite+aiosqlite:///astro_bot.db

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://bothub.chat/api/v2/openai/v1

# Logging
LOG_LEVEL=INFO

# Environment
ENVIRONMENT=production
EOF
    chown solarbot:solarbot /home/solarbot/solarbalance/.env
    chmod 600 /home/solarbot/solarbalance/.env
fi

# Создание systemd сервиса
echo "🔧 Настройка systemd сервиса..."
cat > /etc/systemd/system/solarbalance-bot.service << EOF
[Unit]
Description=Solar Balance Telegram Bot
After=network.target

[Service]
Type=simple
User=solarbot
Group=solarbot
WorkingDirectory=/home/solarbot/solarbalance
Environment=PATH=/home/solarbot/solarbalance/venv/bin
ExecStart=/home/solarbot/solarbalance/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable solarbalance-bot

# Создание директорий
mkdir -p /home/solarbot/solarbalance/logs
chown -R solarbot:solarbot /home/solarbot/solarbalance/logs

echo ""
echo "✅ Быстрый деплой завершен!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Отредактируйте конфигурацию:"
echo "   sudo nano /home/solarbot/solarbalance/.env"
echo ""
echo "2. Добавьте ваши API ключи в .env файл"
echo ""
echo "3. Запустите бота:"
echo "   sudo systemctl start solarbalance-bot"
echo ""
echo "4. Проверьте статус:"
echo "   sudo systemctl status solarbalance-bot"
echo "" 