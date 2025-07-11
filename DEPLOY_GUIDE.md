# 🚀 Руководство по деплою SolarBalance на сервер

## 📋 Обзор

Это руководство поможет вам развернуть SolarBalance бота на Linux сервере с использованием виртуального окружения Python (venv) без Docker.

## 🔧 Системные требования

### Минимальные требования:
- **ОС**: Ubuntu 18.04+, CentOS 7+, Debian 9+
- **Python**: 3.9 или выше
- **RAM**: 512MB (рекомендуется 1GB+)
- **Диск**: 2GB свободного места
- **Сеть**: Доступ к интернету

### Рекомендуемые требования:
- **ОС**: Ubuntu 20.04+ LTS
- **Python**: 3.10+
- **RAM**: 2GB+
- **Диск**: 5GB+
- **CPU**: 1 ядро (рекомендуется 2+)

## 🛠️ Подготовка сервера

### 1. Обновление системы

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 2. Установка Python и зависимостей

```bash
# Ubuntu/Debian
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential libffi-dev libssl-dev git

# CentOS/RHEL
sudo yum install -y python3 python3-pip python3-devel gcc openssl-devel libffi-devel git
```

### 3. Создание пользователя (рекомендуется)

```bash
# Создаем пользователя для бота
sudo useradd -m -s /bin/bash solarbalance
sudo passwd solarbalance

# Переходим к пользователю
sudo su - solarbalance
```

## 📥 Установка бота

### 1. Клонирование репозитория

```bash
# Клонируем проект
git clone <your-repo-url> solarbalance
cd solarbalance

# Или загружаем архив
wget <archive-url>
unzip solarbalance.zip
cd solarbalance
```

### 2. Автоматическая установка

```bash
# Запускаем скрипт автоматической установки
./deploy.sh
```

Скрипт автоматически:
- Проверит версию Python
- Установит системные зависимости
- Создаст виртуальное окружение
- Установит Python зависимости
- Создаст конфигурационные файлы
- Проверит корректность установки

### 3. Ручная установка (если нужно)

```bash
# Создаем виртуальное окружение
python3 -m venv venv

# Активируем окружение
source venv/bin/activate

# Обновляем pip
pip install --upgrade pip setuptools wheel

# Устанавливаем зависимости
pip install -r requirements-prod.txt

# Создаем конфигурационный файл
cp env.example .env
```

## ⚙️ Конфигурация

### 1. Настройка переменных окружения

Отредактируйте файл `.env`:

```bash
nano .env
```

Заполните обязательные поля:

```env
# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN=your_bot_token_here

# ID администраторов (через запятую)
ADMIN_IDS=123456789,987654321

# API ключ для AI прогнозов (Bothub)
AI_API=your_bothub_api_key_here

# База данных (по умолчанию SQLite)
DATABASE_URL=sqlite:///astro_bot.db

# Режим работы
ENVIRONMENT=production
```

### 2. Скачивание файлов эфемерид

```bash
# Скачиваем файлы Swiss Ephemeris
wget https://www.astro.com/ftp/swisseph/ephe/de421.bsp
wget https://www.astro.com/ftp/swisseph/ephe/de422.bsp

# Или используйте другой источник
curl -O https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de421.bsp
```

### 3. Создание директорий

```bash
mkdir -p logs assets pics pictures
```

## 🚀 Запуск бота

### 1. Тестовый запуск

```bash
# Активируем окружение
source venv/bin/activate

# Запускаем бота
python main.py
```

### 2. Запуск через скрипт

```bash
./start_server.sh
```

### 3. Запуск как системный сервис

```bash
# Копируем файл сервиса
sudo cp solarbalance.service /etc/systemd/system/

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable solarbalance

# Запускаем сервис
sudo systemctl start solarbalance

# Проверяем статус
sudo systemctl status solarbalance
```

## 📊 Управление сервисом

### Основные команды:

```bash
# Запуск
sudo systemctl start solarbalance

# Остановка
sudo systemctl stop solarbalance

# Перезапуск
sudo systemctl restart solarbalance

# Статус
sudo systemctl status solarbalance

# Логи
sudo journalctl -u solarbalance -f

# Отключение автозапуска
sudo systemctl disable solarbalance
```

## 📝 Логирование

### Просмотр логов:

```bash
# Системные логи
sudo journalctl -u solarbalance -f

# Логи приложения
tail -f logs/bot.log

# Логи за последний час
sudo journalctl -u solarbalance --since "1 hour ago"
```

## 🔧 Обслуживание

### Обновление бота:

```bash
# Останавливаем сервис
sudo systemctl stop solarbalance

# Переходим в директорию проекта
cd /path/to/solarbalance

# Обновляем код
git pull origin main

# Активируем окружение
source venv/bin/activate

# Обновляем зависимости
pip install -r requirements-prod.txt --upgrade

# Запускаем сервис
sudo systemctl start solarbalance
```

### Резервное копирование:

```bash
# Создаем backup базы данных
cp astro_bot.db astro_bot.db.backup.$(date +%Y%m%d_%H%M%S)

# Создаем архив проекта
tar -czf solarbalance_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    .
```

## 🛡️ Безопасность

### 1. Файрвол

```bash
# Ubuntu (UFW)
sudo ufw allow ssh
sudo ufw allow 8080/tcp  # Если используется webhook
sudo ufw enable

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

### 2. Права доступа

```bash
# Устанавливаем правильные права
chmod 600 .env
chmod 644 *.py
chmod 755 *.sh
```

### 3. Обновления безопасности

```bash
# Настраиваем автоматические обновления
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

## 🚨 Устранение неполадок

### Частые проблемы:

1. **Бот не запускается**
   ```bash
   # Проверяем логи
   sudo journalctl -u solarbalance -n 50
   
   # Проверяем конфигурацию
   source venv/bin/activate
   python -c "from config import Config; print('Config OK')"
   ```

2. **Ошибки зависимостей**
   ```bash
   # Переустанавливаем зависимости
   source venv/bin/activate
   pip install -r requirements-prod.txt --force-reinstall
   ```

3. **Проблемы с базой данных**
   ```bash
   # Проверяем права доступа
   ls -la astro_bot.db
   
   # Создаем новую базу (ОСТОРОЖНО!)
   rm astro_bot.db
   python -c "from database import DatabaseManager; db = DatabaseManager(); print('DB OK')"
   ```

4. **Проблемы с Swiss Ephemeris**
   ```bash
   # Проверяем файлы эфемерид
   ls -la *.bsp
   
   # Скачиваем заново
   wget https://www.astro.com/ftp/swisseph/ephe/de421.bsp
   ```

## 📈 Мониторинг

### Простой мониторинг:

```bash
# Создаем скрипт мониторинга
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    if ! systemctl is-active --quiet solarbalance; then
        echo "$(date): Bot is down, restarting..."
        systemctl restart solarbalance
    fi
    sleep 60
done
EOF

chmod +x monitor.sh
```

### Настройка логротации:

```bash
sudo nano /etc/logrotate.d/solarbalance
```

```
/home/solarbalance/solarbalance/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 solarbalance solarbalance
}
```

## 🎯 Оптимизация производительности

### 1. Настройка systemd сервиса

```ini
[Unit]
Description=SolarBalance Astrology Telegram Bot
After=network.target

[Service]
Type=simple
User=solarbalance
WorkingDirectory=/home/solarbalance/solarbalance
Environment=PATH=/home/solarbalance/solarbalance/venv/bin
ExecStart=/home/solarbalance/solarbalance/venv/bin/python /home/solarbalance/solarbalance/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Ограничения ресурсов
MemoryMax=1G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

### 2. Настройка PostgreSQL (опционально)

```bash
# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib

# Создание базы данных
sudo -u postgres createdb solarbalance
sudo -u postgres createuser solarbalance
sudo -u postgres psql -c "ALTER USER solarbalance WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE solarbalance TO solarbalance;"

# Обновляем .env
DATABASE_URL=postgresql://solarbalance:password@localhost:5432/solarbalance
```

## ✅ Чек-лист деплоя

- [ ] Сервер подготовлен и обновлен
- [ ] Python 3.9+ установлен
- [ ] Код проекта загружен
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] Файл .env настроен
- [ ] Файлы эфемерид скачаны
- [ ] Тестовый запуск прошел успешно
- [ ] Systemd сервис настроен
- [ ] Автозапуск включен
- [ ] Логирование работает
- [ ] Резервное копирование настроено
- [ ] Мониторинг настроен

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `sudo journalctl -u solarbalance -f`
2. Проверьте конфигурацию: `source venv/bin/activate && python -c "from config import Config"`
3. Проверьте зависимости: `pip list`
4. Создайте Issue в репозитории с описанием проблемы

---

**Удачного деплоя! 🚀** 