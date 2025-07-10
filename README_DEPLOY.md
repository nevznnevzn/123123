# 🚀 Развертывание SolarBalance на сервере (без Docker)

## 📋 Краткий обзор

Эта инструкция поможет вам развернуть астрологический Telegram-бот SolarBalance на вашем сервере с использованием виртуального окружения Python (venv).

## ⚡ Быстрый старт

### 1. Подготовьте данные
- 🤖 **Токен бота** - получите у [@BotFather](https://t.me/BotFather)
- 🔑 **API ключ** - [Bothub](https://bothub.chat) или [OpenAI](https://platform.openai.com)
- 👤 **Ваш Telegram ID** - получите у [@userinfobot](https://t.me/userinfobot)

### 2. Автоматическая установка (рекомендуется)
```bash
# Загрузите скрипт автоустановки
wget https://raw.githubusercontent.com/YOUR_USERNAME/solarbalance/main/install_server.sh
chmod +x install_server.sh

# Запустите установку
sudo ./install_server.sh
```

### 3. Настройте конфигурацию
```bash
# Отредактируйте файл конфигурации
sudo nano /home/solarbalance/solarbalance-bot/.env
```

Обязательно заполните:
```env
BOT_TOKEN=ваш_токен_от_BotFather
AI_API=ваш_ключ_bothub_или_openai
ADMIN_IDS=ваш_telegram_id
```

### 4. Запустите бота
```bash
# Запуск
sudo systemctl start solarbalance

# Проверка статуса
sudo systemctl status solarbalance

# Просмотр логов
sudo journalctl -u solarbalance -f
```

## 📚 Подробные инструкции

- 📖 **[Полная инструкция](deploy_server.md)** - детальное руководство
- ⚡ **[Быстрый деплой](QUICK_DEPLOY.md)** - краткие инструкции
- 🔍 **Проверка системы**: `./check_system.sh`

## 🛠️ Управление ботом

### Основные команды
```bash
# Управление сервисом
sudo systemctl start solarbalance    # Запуск
sudo systemctl stop solarbalance     # Остановка
sudo systemctl restart solarbalance  # Перезапуск
sudo systemctl status solarbalance   # Статус

# Логи
sudo journalctl -u solarbalance -f   # Просмотр логов в реальном времени
sudo journalctl -u solarbalance --since "1 hour ago"  # Логи за час

# Мониторинг (после установки)
/home/solarbalance/solarbalance-bot/monitor.sh

# Обновление (после установки)
/home/solarbalance/solarbalance-bot/update_bot.sh
```

### Файлы и пути
```
/home/solarbalance/solarbalance-bot/     # Основная директория
├── .env                                 # Конфигурация
├── logs/                               # Логи приложения
├── venv/                               # Python окружение
├── main_simple.py                      # Основной файл запуска
├── monitor.sh                          # Скрипт мониторинга
└── update_bot.sh                       # Скрипт обновления

/etc/systemd/system/solarbalance.service # Systemd сервис
```

## 🔧 Конфигурация

### Обязательные переменные окружения
```env
# Telegram Bot
BOT_TOKEN=your_bot_token_here

# AI Service  
AI_API=your_bothub_or_openai_key

# Admin Access
ADMIN_IDS=123456789,987654321
```

### Опциональные переменные
```env
# Database (по умолчанию SQLite)
DATABASE_URL=sqlite+aiosqlite:///solarbalance.db

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# PostgreSQL (для продакшена)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/solarbalance
```

## 🗄️ База данных

### SQLite (по умолчанию)
- ✅ Простая настройка
- ✅ Не требует дополнительных сервисов
- ⚠️ Ограничения производительности при высокой нагрузке

### PostgreSQL (рекомендуется для продакшена)
```bash
# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib

# Создание базы данных
sudo -u postgres createdb solarbalance
sudo -u postgres createuser solarbalance_user

# Настройка в .env
DATABASE_URL=postgresql+asyncpg://solarbalance_user:password@localhost/solarbalance
```

## 📊 Проверка работы

### Тестирование функций
1. **Запуск бота**: Напишите `/start` в Telegram
2. **Админ-панель**: Команда `/admin` (только для администраторов)
3. **Создание карты**: Заполните профиль и создайте натальную карту
4. **Прогнозы**: Попробуйте получить прогноз
5. **Звёздный совет**: Задайте вопрос боту

### Мониторинг
```bash
# Статус сервиса
sudo systemctl is-active solarbalance

# Использование ресурсов
ps aux | grep solarbalance

# Размер базы данных
du -sh /home/solarbalance/solarbalance-bot/solarbalance.db

# Логи ошибок
sudo journalctl -u solarbalance | grep ERROR
```

## 🔐 Безопасность

### Рекомендации
- 🔒 Используйте отдельного пользователя `solarbalance`
- 🔑 Установите права `600` на файл `.env`
- 🛡️ Настройте файрвол (UFW рекомендуется)
- 📋 Регулярно обновляйте систему и зависимости
- 💾 Настройте резервное копирование базы данных

### Настройка файрвола
```bash
# Установка и настройка UFW
sudo apt install ufw
sudo ufw allow ssh
sudo ufw enable

# Для PostgreSQL (если используется)
sudo ufw allow 5432/tcp
```

## 🔄 Обновления

### Автоматическое обновление
```bash
# Используйте готовый скрипт
/home/solarbalance/solarbalance-bot/update_bot.sh
```

### Ручное обновление
```bash
# Остановите бота
sudo systemctl stop solarbalance

# Перейдите в директорию проекта
cd /home/solarbalance/solarbalance-bot

# Активируйте окружение
source venv/bin/activate

# Получите обновления
git pull origin main

# Обновите зависимости
pip install -e .

# Запустите бота
sudo systemctl start solarbalance
```

## 🆘 Устранение проблем

### Типичные проблемы

**1. Бот не запускается**
```bash
# Проверьте логи
sudo journalctl -u solarbalance -f

# Проверьте конфигурацию
cat /home/solarbalance/solarbalance-bot/.env

# Проверьте Python окружение
su - solarbalance
cd solarbalance-bot
source venv/bin/activate
python -c "import aiogram; print('OK')"
```

**2. Ошибки ИИ**
```bash
# Проверьте API ключ
grep AI_API /home/solarbalance/solarbalance-bot/.env

# Проверьте доступность API
curl -s "https://bothub.chat/api/health" || curl -s "https://api.openai.com/"
```

**3. Проблемы с базой данных**
```bash
# Проверьте права доступа
ls -la /home/solarbalance/solarbalance-bot/solarbalance.db

# Проверьте размер базы
du -sh /home/solarbalance/solarbalance-bot/solarbalance.db

# Для PostgreSQL - проверьте соединение
psql $DATABASE_URL -c "SELECT 1;"
```

**4. Высокое потребление ресурсов**
```bash
# Перезапустите сервис
sudo systemctl restart solarbalance

# Проверьте использование памяти
ps aux | grep solarbalance

# Очистите логи
sudo journalctl --vacuum-time=7d
```

## 📈 Производительность

### Оптимизация
- 💾 Используйте PostgreSQL для больших нагрузок
- 🗄️ Настройте Redis для кэширования (в планах)
- 📊 Мониторьте использование ресурсов
- 🧹 Регулярно очищайте старые логи и данные

### Рекомендуемые ресурсы сервера
- **Минимум**: 1 CPU, 2GB RAM, 10GB диск
- **Рекомендуется**: 2 CPU, 4GB RAM, 20GB диск
- **Высокая нагрузка**: 4+ CPU, 8GB+ RAM, SSD диск

## 📞 Поддержка

### При возникновении проблем:
1. 📋 Соберите информацию:
   ```bash
   # Системная информация
   ./check_system.sh > system_info.txt
   
   # Логи
   sudo journalctl -u solarbalance > bot_logs.txt
   
   # Конфигурация (без паролей!)
   grep -v "TOKEN\|API\|PASSWORD" .env > config_info.txt
   ```

2. 🔍 Проверьте документацию:
   - [Полная инструкция](deploy_server.md)
   - [Быстрый деплой](QUICK_DEPLOY.md)

3. 📧 Обратитесь за помощью с собранной информацией

---

## ✅ Чек-лист развертывания

- [ ] Подготовлен сервер (Ubuntu 20.04+/Debian 11+/CentOS 8+)
- [ ] Получен токен бота от @BotFather
- [ ] Получен API ключ Bothub/OpenAI
- [ ] Узнан ваш Telegram ID
- [ ] Запущена проверка системы: `./check_system.sh`
- [ ] Выполнена установка: `sudo ./install_server.sh`
- [ ] Настроен файл `.env`
- [ ] Запущен сервис: `systemctl start solarbalance`
- [ ] Проверена работа: команда `/start` в Telegram
- [ ] Настроен файрвол
- [ ] Протестированы основные функции

**🎉 Поздравляем! Ваш бот SolarBalance готов к работе!** 