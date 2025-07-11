# 🚀 Быстрый деплой SolarBalance

## 📋 Что подготовлено

✅ **Файлы для деплоя:**
- `deploy.sh` - Автоматический скрипт деплоя
- `start_server.sh` - Скрипт запуска бота  
- `requirements-prod.txt` - Продакшен зависимости
- `env.example` - Пример переменных окружения
- `check_deploy.py` - Проверка готовности к деплою
- `DEPLOY_GUIDE.md` - Подробное руководство
- `solarbalance.service` - Systemd сервис (создается автоматически)

✅ **Улучшения:**
- Продакшен-готовая конфигурация в `config.py`
- Улучшенное логирование в `main.py`
- Graceful shutdown и обработка ошибок
- Проверка переменных окружения
- Поддержка PostgreSQL и SQLite

## 🎯 Быстрый старт

### 1. Проверка готовности
```bash
python check_deploy.py
```

### 2. Автоматический деплой
```bash
./deploy.sh
```

### 3. Настройка переменных
```bash
nano .env
# Укажите BOT_TOKEN, ADMIN_IDS, AI_API
```

### 4. Запуск
```bash
# Тестовый запуск
./start_server.sh

# Или как сервис
sudo systemctl start solarbalance
```

## ⚙️ Обязательные переменные

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321
AI_API=your_bothub_api_key
```

## 🔧 Системные требования

- **Python 3.9+**
- **RAM:** 1GB+ (рекомендуется 2GB+)
- **Диск:** 2GB+ свободного места
- **ОС:** Ubuntu 18.04+, CentOS 7+, Debian 9+

## 📂 Структура после деплоя

```
solarbalance/
├── venv/                    # Виртуальное окружение
├── logs/                    # Логи приложения
├── .env                     # Переменные окружения
├── astro_bot.db            # База данных SQLite
├── de421.bsp, de422.bsp    # Файлы эфемерид (скачать)
└── solarbalance.service    # Systemd сервис
```

## 🛠️ Управление сервисом

```bash
# Статус
sudo systemctl status solarbalance

# Запуск/остановка
sudo systemctl start solarbalance
sudo systemctl stop solarbalance

# Логи
sudo journalctl -u solarbalance -f

# Автозапуск
sudo systemctl enable solarbalance
```

## 🚨 Важные моменты

1. **Скачайте файлы эфемерид:**
   ```bash
   wget https://www.astro.com/ftp/swisseph/ephe/de421.bsp
   wget https://www.astro.com/ftp/swisseph/ephe/de422.bsp
   ```

2. **Настройте права доступа:**
   ```bash
   chmod 600 .env
   chmod +x *.sh
   ```

3. **Для продакшена используйте PostgreSQL:**
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/solarbalance
   ```

## 📞 Поддержка

- Подробное руководство: `DEPLOY_GUIDE.md`
- Проверка готовности: `python check_deploy.py`
- Логи ошибок: `sudo journalctl -u solarbalance -n 50`

---

**Готов к деплою! 🎉** 