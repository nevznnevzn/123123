# 🚀 Полное руководство по деплою Solar Balance Bot

## 📋 Подготовка к деплою

### Необходимые данные:
- 🤖 **Токен бота** - получите у [@BotFather](https://t.me/BotFather)
- 🔑 **API ключ** - [Bothub](https://bothub.chat) или [OpenAI](https://platform.openai.com)
- 💻 **Сервер** - Ubuntu 20.04+, Debian 11+, CentOS 8+ или VPS

## 🖥️ Подготовка проекта (Windows/Linux)

### 1. Подготовьте файлы для деплоя
```bash
# Убедитесь, что все файлы готовы
ls -la *.py *.sh *.md requirements*.txt
```

### 2. Создайте архив для загрузки на сервер
```bash
# На Windows (PowerShell)
Compress-Archive -Path . -DestinationPath solarbalance-deploy.zip -Force

# На Linux
tar -czf solarbalance-deploy.tar.gz .
```

## 🚀 Деплой на сервер

### Вариант 1: Автоматическая установка (рекомендуется)

1. **Загрузите проект на сервер:**
   ```bash
   # Через SCP
   scp solarbalance-deploy.zip user@your-server:/tmp/
   
   # Или через Git
   git clone <your-repo-url>
   cd solarbalance
   ```

2. **Запустите автоматическую установку:**
   ```bash
   # Распакуйте архив (если нужно)
   unzip /tmp/solarbalance-deploy.zip -d /tmp/solarbalance
   cd /tmp/solarbalance
   
   # Запустите установку
   sudo bash install_server.sh
   ```

### Вариант 2: Обновление существующей установки
```bash
# Если бот уже установлен на сервере
sudo bash update_existing.sh
```

### Вариант 3: Быстрый деплой
```bash
# Для опытных пользователей
sudo bash quick_deploy.sh
```

### Вариант 4: Ручная установка
Следуйте подробному руководству в файле `deploy_server.md`

## ⚙️ Настройка после установки

### 1. Отредактируйте конфигурацию
```bash
sudo nano /home/solarbot/solarbalance/.env
```

**Обязательные настройки:**
```env
# Telegram Bot Token
BOT_TOKEN=your_bot_token_from_botfather

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://bothub.chat/api/v2/openai/v1

# Database (SQLite по умолчанию)
DATABASE_URL=sqlite+aiosqlite:///astro_bot.db

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 2. Запустите бота
```bash
# Запуск
sudo systemctl start solarbalance-bot

# Проверка статуса
sudo systemctl status solarbalance-bot

# Просмотр логов
sudo journalctl -u solarbalance-bot -f
```

## 🔧 Управление ботом

### Основные команды
```bash
# Запуск/остановка
sudo systemctl start solarbalance-bot
sudo systemctl stop solarbalance-bot
sudo systemctl restart solarbalance-bot

# Статус и логи
sudo systemctl status solarbalance-bot
sudo journalctl -u solarbalance-bot -f

# Мониторинг
check-solarbot
update-solarbot
```

### Полезные команды
```bash
# Проверка процесса
ps aux | grep python | grep solarbalance

# Размер логов
du -sh /home/solarbot/solarbalance/logs/

# Последние ошибки
sudo journalctl -u solarbalance-bot --since "1 hour ago" | grep -i error
```

## 🗄️ Настройка базы данных

### SQLite (по умолчанию)
```env
DATABASE_URL=sqlite+aiosqlite:///astro_bot.db
```

### PostgreSQL (рекомендуется для продакшена)
```bash
# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib libpq-dev

# Создание базы данных
sudo -u postgres psql
CREATE DATABASE solarbalance;
CREATE USER solarbot WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE solarbalance TO solarbot;
\q

# Обновление .env
DATABASE_URL=postgresql+asyncpg://solarbot:your_password@localhost/solarbalance
```

## 🛡️ Безопасность

### Настройка файрвола
```bash
# Установка UFW
sudo apt install ufw

# Настройка правил
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 22

# Включение файрвола
sudo ufw enable
```

### Настройка SSH
```bash
# Отключение root логина
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no

# Перезапуск SSH
sudo systemctl restart ssh
```

## 📊 Мониторинг и логи

### Просмотр логов
```bash
# Логи systemd
sudo journalctl -u solarbalance-bot -f

# Логи приложения
tail -f /home/solarbot/solarbalance/logs/bot.log

# Логи за последний час
sudo journalctl -u solarbalance-bot --since "1 hour ago"
```

### Ротация логов
Логи автоматически ротируются через `/etc/logrotate.d/solarbalance-bot`

## 🔄 Обновление бота

### Обновление существующей установки (рекомендуется)
```bash
# Автоматическое обновление с резервным копированием
sudo bash update_existing.sh
```

### Автоматическое обновление (если скрипты установлены)
```bash
update-solarbot
```

### Ручное обновление
```bash
# Остановка
sudo systemctl stop solarbalance-bot

# Обновление кода
cd /home/solarbot/solarbalance
git pull origin main

# Обновление зависимостей
source venv/bin/activate
pip install -r requirements-prod.txt --upgrade

# Запуск
sudo systemctl start solarbalance-bot
```

### Резервное копирование перед обновлением
```bash
# Создание резервной копии
sudo cp /home/solarbot/solarbalance/.env /tmp/solarbalance_backup.env
sudo cp /home/solarbot/solarbalance/astro_bot.db /tmp/solarbalance_backup.db

# Восстановление (если что-то пошло не так)
sudo cp /tmp/solarbalance_backup.env /home/solarbot/solarbalance/.env
sudo cp /tmp/solarbalance_backup.db /home/solarbot/solarbalance/astro_bot.db
```

## 🆘 Устранение проблем

### Бот не запускается
```bash
# Проверьте логи
sudo journalctl -u solarbalance-bot -n 50

# Проверьте конфигурацию
cat /home/solarbot/solarbalance/.env

# Проверьте права
ls -la /home/solarbot/solarbalance/
```

### Проблемы с зависимостями
```bash
# Переустановка зависимостей
sudo su - solarbot
cd /home/solarbot/solarbalance
source venv/bin/activate
pip install -r requirements-prod.txt --force-reinstall
```

### Проблемы с базой данных
```bash
# Для SQLite
ls -la /home/solarbot/solarbalance/astro_bot.db

# Для PostgreSQL
sudo -u postgres psql -d solarbalance -c "SELECT 1;"
```

### Высокое потребление ресурсов
```bash
# Перезапуск сервиса
sudo systemctl restart solarbalance-bot

# Очистка логов
sudo journalctl --vacuum-time=7d
```

## 📈 Производительность

### Рекомендуемые ресурсы сервера
- **Минимум**: 1 CPU, 512MB RAM, 2GB диск
- **Рекомендуется**: 2 CPU, 1GB RAM, 5GB диск
- **Высокая нагрузка**: 4+ CPU, 4GB+ RAM, SSD диск

### Оптимизация
- Используйте PostgreSQL для больших нагрузок
- Настройте регулярную очистку логов
- Мониторьте использование ресурсов

## ✅ Чек-лист деплоя

- [ ] Подготовлен сервер (Ubuntu 20.04+/Debian 11+)
- [ ] Получен токен бота от @BotFather
- [ ] Получен API ключ Bothub/OpenAI
- [ ] Запущена автоматическая установка
- [ ] Настроен файл `.env`
- [ ] Запущен сервис `solarbalance-bot`
- [ ] Проверена работа бота в Telegram
- [ ] Настроен файрвол
- [ ] Протестированы основные функции

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u solarbalance-bot -f`
2. Проверьте статус: `sudo systemctl status solarbalance-bot`
3. Проверьте конфигурацию в файле `.env`
4. Убедитесь, что все зависимости установлены

---

**🎉 Поздравляем! Ваш Solar Balance Bot готов к работе! 🚀** 