# 🔧 Исправление проблем с сервером SolarBalance

## 🚨 Основная проблема

Бот не запускается из-за ошибки: **"Token is invalid!"**

## 📋 Пошаговое решение

### 1. Подключитесь к серверу и перейдите в директорию проекта

```bash
ssh your_user@your_server_ip
cd /opt/solarbalance
```

### 2. Загрузите и запустите скрипт исправления

```bash
# Загрузить скрипт исправления из репозитория
wget https://raw.githubusercontent.com/nevznnevzn/123123/main/fix_server_config.sh

# Или скопировать из локального проекта
# scp fix_server_config.sh your_user@your_server_ip:/opt/solarbalance/

# Сделать скрипт исполняемым
chmod +x fix_server_config.sh

# Запустить скрипт
sudo ./fix_server_config.sh
```

### 3. Ручное исправление (если скрипт недоступен)

#### 3.1. Создать/исправить .env файл

```bash
cd /opt/solarbalance

# Создать .env файл из примера
cp env.example .env

# Исправить права доступа
chmod 600 .env
chmod +x start_server.sh
chmod +x deploy.sh
```

#### 3.2. Получить токен Telegram бота

1. Откройте Telegram и найдите **@BotFather**
2. Отправьте команду `/mybots` чтобы увидеть существующих ботов
3. Выберите вашего бота или создайте нового с `/newbot`
4. Получите токен командой `/token` (для существующего бота)

**Токен должен выглядеть так:** `123456789:AABCDefGhIJKlmNOPqrsTUVwxyZ`

#### 3.3. Настроить .env файл

```bash
# Редактировать .env файл
nano .env

# Установить токен бота
BOT_TOKEN=ВАШ_РЕАЛЬНЫЙ_ТОКЕН_ЗДЕСЬ
TELEGRAM_BOT_TOKEN=ВАШ_РЕАЛЬНЫЙ_ТОКЕН_ЗДЕСЬ

# Установить ваш Telegram ID (узнать можно у @userinfobot)
ADMIN_IDS=ВАШ_TELEGRAM_ID

# Сгенерировать SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)
```

#### 3.4. Перезапустить сервис

```bash
# Остановить сервис
sudo systemctl stop solarbalance

# Запустить сервис
sudo systemctl start solarbalance

# Проверить статус
sudo systemctl status solarbalance
```

### 4. Проверка работы

```bash
# Посмотреть логи в реальном времени
sudo journalctl -u solarbalance -f

# Посмотреть последние 20 строк логов
sudo journalctl -u solarbalance -n 20 --no-pager

# Проверить статус сервиса
sudo systemctl status solarbalance
```

## ✅ Признаки успешного запуска

В логах должно появиться:
```
✅ База данных инициализирована
✅ Все обработчики зарегистрированы
🚀 Бот запущен и готов к работе!
```

## 🚨 Возможные проблемы и решения

### Проблема: "Token is invalid!"

**Причины:**
- Неправильный токен в .env файле
- Токен скопирован с лишними символами
- Бот уже используется в другом месте

**Решение:**
1. Получите новый токен у @BotFather
2. Убедитесь что токен скопирован точно без пробелов
3. Остановите бота в других местах если он там запущен

### Проблема: "Permission denied"

**Решение:**
```bash
chmod +x /opt/solarbalance/start_server.sh
chmod 600 /opt/solarbalance/.env
```

### Проблема: Сервис постоянно перезапускается

**Проверка:**
```bash
sudo journalctl -u solarbalance -n 50 --no-pager
```

**Возможные причины:**
- Ошибки в коде
- Неправильная конфигурация
- Отсутствие зависимостей

### Проблема: "Module not found"

**Решение:**
```bash
cd /opt/solarbalance
source venv/bin/activate
pip install -r requirements-prod.txt
```

## 🎯 Быстрые команды для управления

```bash
# Статус
sudo systemctl status solarbalance

# Запуск
sudo systemctl start solarbalance

# Остановка
sudo systemctl stop solarbalance

# Перезапуск
sudo systemctl restart solarbalance

# Логи в реальном времени
sudo journalctl -u solarbalance -f

# Последние 50 строк логов
sudo journalctl -u solarbalance -n 50 --no-pager

# Отключить автозапуск
sudo systemctl disable solarbalance

# Включить автозапуск
sudo systemctl enable solarbalance
```

## 📞 Тестирование бота

После успешного запуска:

1. Найдите вашего бота в Telegram по имени
2. Отправьте команду `/start`
3. Бот должен ответить приветственным сообщением

## 🔍 Диагностика проблем

Если бот не отвечает:

1. **Проверьте логи:**
   ```bash
   sudo journalctl -u solarbalance -n 50 --no-pager
   ```

2. **Проверьте сетевое соединение:**
   ```bash
   curl -s https://api.telegram.org/bot$BOT_TOKEN/getMe
   ```

3. **Проверьте конфигурацию:**
   ```bash
   cd /opt/solarbalance
   python3 check_deploy.py
   ```

## 📧 Получение помощи

Если проблемы продолжаются, отправьте:

1. Вывод `sudo systemctl status solarbalance`
2. Последние 30 строк логов: `sudo journalctl -u solarbalance -n 30 --no-pager`
3. Результат проверки: `python3 check_deploy.py`

---

**⚠️ Важно:** Никогда не передавайте токен бота третьим лицам! 