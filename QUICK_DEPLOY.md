# ⚡ Быстрое развертывание SolarBalance

## 🚀 Автоматическая установка (рекомендуется)

### 1. Подготовка
Убедитесь, что у вас есть:
- ✅ Сервер с Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- ✅ SSH доступ с правами root
- ✅ Токен Telegram бота (получите у @BotFather)
- ✅ API ключ Bothub или OpenAI
- ✅ Ваш Telegram ID (получите у @userinfobot)

### 2. Одна команда для установки
```bash
# Загрузите и запустите скрипт автоустановки
wget https://raw.githubusercontent.com/YOUR_USERNAME/solarbalance/main/install_server.sh
chmod +x install_server.sh
sudo ./install_server.sh
```

### 3. Настройка
```bash
# Отредактируйте конфигурацию
sudo nano /home/solarbalance/solarbalance-bot/.env
```

Заполните обязательные поля:
```env
BOT_TOKEN=ваш_токен_от_BotFather
AI_API=ваш_ключ_bothub_или_openai
ADMIN_IDS=ваш_telegram_id
```

### 4. Запуск
```bash
# Запустите бота
sudo systemctl start solarbalance

# Проверьте статус
sudo systemctl status solarbalance

# Посмотрите логи
sudo journalctl -u solarbalance -f
```

---

## 🔧 Ручная установка

### 1. Подготовка сервера
```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем зависимости
sudo apt install -y python3 python3-pip python3-venv git curl wget build-essential python3-dev

# Создаем пользователя
sudo useradd -m -s /bin/bash solarbalance
sudo su - solarbalance
```

### 2. Установка проекта
```bash
# Клонируем репозиторий
git clone https://github.com/YOUR_USERNAME/solarbalance.git solarbalance-bot
cd solarbalance-bot

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -e .
```

### 3. Конфигурация
```bash
# Создаем конфигурацию
cp env.example .env
nano .env

# Создаем директории
mkdir -p logs assets
```

### 4. Systemd сервис
```bash
# Выходим из пользователя solarbalance
exit

# Создаем сервис
sudo nano /etc/systemd/system/solarbalance.service
```

Содержимое файла:
```ini
[Unit]
Description=SolarBalance Astrology Telegram Bot
After=network.target

[Service]
Type=simple
User=solarbalance
WorkingDirectory=/home/solarbalance/solarbalance-bot
Environment=PATH=/home/solarbalance/solarbalance-bot/venv/bin
ExecStart=/home/solarbalance/solarbalance-bot/venv/bin/python main_simple.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5. Запуск
```bash
sudo systemctl daemon-reload
sudo systemctl enable solarbalance
sudo systemctl start solarbalance
```

---

## 📊 Управление

### Основные команды
```bash
# Запуск/остановка/перезапуск
sudo systemctl start solarbalance
sudo systemctl stop solarbalance
sudo systemctl restart solarbalance

# Статус и логи
sudo systemctl status solarbalance
sudo journalctl -u solarbalance -f

# Мониторинг
/home/solarbalance/solarbalance-bot/monitor.sh

# Обновление
/home/solarbalance/solarbalance-bot/update_bot.sh
```

### Проверка работы
1. Напишите боту `/start` в Telegram
2. Проверьте админ-панель командой `/admin`
3. Создайте тестовую натальную карту

---

## 🆘 Решение проблем

### Бот не запускается
```bash
# Проверьте логи
sudo journalctl -u solarbalance -f

# Проверьте конфигурацию
cat /home/solarbalance/solarbalance-bot/.env

# Проверьте зависимости
su - solarbalance
cd solarbalance-bot
source venv/bin/activate
python -c "import aiogram, openai; print('OK')"
```

### Бот не отвечает
```bash
# Проверьте токен
grep BOT_TOKEN /home/solarbalance/solarbalance-bot/.env

# Проверьте соединение
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe"
```

### Ошибки ИИ
```bash
# Проверьте API ключ
grep AI_API /home/solarbalance/solarbalance-bot/.env

# Проверьте баланс Bothub/OpenAI
```

---

## 📞 Поддержка

При проблемах:
1. 📋 Соберите логи: `sudo journalctl -u solarbalance > logs.txt`
2. ⚙️ Проверьте конфигурацию: `cat .env`
3. 🔍 Проверьте статус: `systemctl status solarbalance`

**Время развертывания: 5-10 минут** ⏱️ 