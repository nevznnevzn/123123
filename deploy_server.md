# 🚀 Руководство по деплою Solar Balance Bot на сервер

## 📋 Требования к серверу

- **ОС:** Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **Python:** 3.9+ (рекомендуется 3.11+)
- **RAM:** минимум 512MB (рекомендуется 1GB+)
- **Диск:** минимум 2GB свободного места
- **Сеть:** стабильное интернет-соединение

## 🔧 Подготовка сервера

### 1. Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Установка Python и зависимостей
```bash
# Установка Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# Установка системных зависимостей
sudo apt install git curl wget build-essential libssl-dev libffi-dev -y

# Для PostgreSQL (если используется)
sudo apt install postgresql postgresql-contrib libpq-dev -y
```

### 3. Создание пользователя для бота
```bash
# Создаем пользователя
sudo useradd -m -s /bin/bash solarbot
sudo usermod -aG sudo solarbot

# Переключаемся на пользователя
sudo su - solarbot
```

## 📥 Установка бота

### 1. Клонирование репозитория
```bash
cd /home/solarbot
git clone https://github.com/your-username/solarbalance.git
cd solarbalance
```

### 2. Создание виртуального окружения
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей
```bash
# Обновляем pip
pip install --upgrade pip

# Устанавливаем зависимости
pip install -r requirements-prod.txt
```

### 4. Настройка конфигурации
```bash
# Копируем пример конфигурации
cp env.example .env

# Редактируем конфигурацию
nano .env
```

**Содержимое .env файла:**
```env
# Telegram Bot Token
BOT_TOKEN=your_bot_token_here

# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost/solarbalance
# или для SQLite:
# DATABASE_URL=sqlite+aiosqlite:///astro_bot.db

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://bothub.chat/api/v2/openai/v1

# Logging
LOG_LEVEL=INFO

# Environment
ENVIRONMENT=production
```

### 5. Настройка базы данных

#### Для PostgreSQL:
```bash
# Создаем базу данных
sudo -u postgres psql
CREATE DATABASE solarbalance;
CREATE USER solarbot WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE solarbalance TO solarbot;
\q

# Применяем миграции (если есть)
python scripts/migrate_to_postgresql.py
```

#### Для SQLite:
```bash
# База данных создастся автоматически при первом запуске
```

## 🚀 Запуск бота

### 1. Тестовый запуск
```bash
# Активируем venv
source venv/bin/activate

# Запускаем бота
python main.py
```

### 2. Настройка systemd сервиса
```bash
# Создаем файл сервиса
sudo nano /etc/systemd/system/solarbalance-bot.service
```

**Содержимое сервиса:**
```ini
[Unit]
Description=Solar Balance Telegram Bot
After=network.target postgresql.service
Wants=postgresql.service

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
```

### 3. Активация сервиса
```bash
# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable solarbalance-bot

# Запускаем сервис
sudo systemctl start solarbalance-bot

# Проверяем статус
sudo systemctl status solarbalance-bot
```

## 📊 Мониторинг и логи

### Просмотр логов
```bash
# Логи systemd
sudo journalctl -u solarbalance-bot -f

# Логи приложения
tail -f /home/solarbot/solarbalance/logs/bot.log
```

### Управление сервисом
```bash
# Остановка
sudo systemctl stop solarbalance-bot

# Перезапуск
sudo systemctl restart solarbalance-bot

# Перезагрузка конфигурации
sudo systemctl reload solarbalance-bot
```

## 🔄 Обновление бота

### 1. Остановка сервиса
```bash
sudo systemctl stop solarbalance-bot
```

### 2. Обновление кода
```bash
cd /home/solarbot/solarbalance
git pull origin main
```

### 3. Обновление зависимостей
```bash
source venv/bin/activate
pip install -r requirements-prod.txt --upgrade
```

### 4. Запуск сервиса
```bash
sudo systemctl start solarbalance-bot
```

## 🛡️ Безопасность

### 1. Настройка файрвола
```bash
# Устанавливаем ufw
sudo apt install ufw

# Настраиваем правила
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 22

# Включаем файрвол
sudo ufw enable
```

### 2. Настройка SSH
```bash
# Отключаем root логин
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no

# Перезапускаем SSH
sudo systemctl restart ssh
```

### 3. Регулярные обновления
```bash
# Создаем скрипт для автоматических обновлений
sudo nano /etc/cron.weekly/update-system
```

## 📈 Мониторинг производительности

### 1. Установка мониторинга
```bash
# Устанавливаем htop для мониторинга
sudo apt install htop

# Устанавливаем netdata (опционально)
bash <(curl -Ss https://my-netdata.io/kickstart.sh)
```

### 2. Настройка алертов
```bash
# Создаем скрипт проверки состояния бота
sudo nano /home/solarbot/check_bot.sh
```

## 🔧 Устранение неполадок

### Частые проблемы:

1. **Бот не запускается:**
   ```bash
   sudo journalctl -u solarbalance-bot -n 50
   ```

2. **Проблемы с базой данных:**
   ```bash
   # Проверяем подключение к PostgreSQL
   sudo -u postgres psql -d solarbalance
   ```

3. **Проблемы с правами:**
   ```bash
   # Проверяем права на файлы
   sudo chown -R solarbot:solarbot /home/solarbot/solarbalance
   ```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u solarbalance-bot -f`
2. Проверьте статус сервиса: `sudo systemctl status solarbalance-bot`
3. Проверьте конфигурацию в файле `.env`
4. Убедитесь, что все зависимости установлены

---

**Успешного деплоя! 🚀** 