# 🚀 Деплой Solar Balance Bot на сервер

## 📋 Быстрый старт

### Вариант 1: Автоматическая установка (рекомендуется)
```bash
# Скачайте проект на сервер
git clone <your-repo-url>
cd solarbalance

# Запустите автоматическую установку
sudo bash install_server.sh
```

### Вариант 2: Быстрый деплой
```bash
# Для опытных пользователей
sudo bash quick_deploy.sh
```

### Вариант 3: Ручная установка
Следуйте подробному руководству в файле `deploy_server.md`

## ⚙️ Настройка после установки

1. **Отредактируйте конфигурацию:**
   ```bash
   sudo nano /home/solarbot/solarbalance/.env
   ```

2. **Добавьте ваши API ключи:**
   ```env
   BOT_TOKEN=your_bot_token_from_botfather
   OPENAI_API_KEY=your_openai_api_key
   ```

3. **Запустите бота:**
   ```bash
   sudo systemctl start solarbalance-bot
   ```

4. **Проверьте статус:**
   ```bash
   sudo systemctl status solarbalance-bot
   ```

## 🔧 Управление ботом

```bash
# Запуск
sudo systemctl start solarbalance-bot

# Остановка
sudo systemctl stop solarbalance-bot

# Перезапуск
sudo systemctl restart solarbalance-bot

# Статус
sudo systemctl status solarbalance-bot

# Логи
sudo journalctl -u solarbalance-bot -f
```

## 📊 Мониторинг

```bash
# Проверка состояния
check-solarbot

# Обновление бота
update-solarbot
```

## 🛡️ Безопасность

- Бот запускается под отдельным пользователем `solarbot`
- Конфигурационные файлы защищены правами 600
- Логи ротируются автоматически
- Systemd обеспечивает автоперезапуск при сбоях

## 📁 Структура файлов

```
/home/solarbot/solarbalance/
├── main.py                 # Главный файл бота
├── .env                    # Конфигурация (защищен)
├── venv/                   # Виртуальное окружение
├── logs/                   # Логи приложения
├── requirements-prod.txt   # Зависимости для продакшена
└── ...
```

## 🔄 Обновление

```bash
# Автоматическое обновление
update-solarbot

# Или вручную
cd /home/solarbot/solarbalance
git pull origin main
source venv/bin/activate
pip install -r requirements-prod.txt --upgrade
sudo systemctl restart solarbalance-bot
```

## 🆘 Устранение проблем

### Бот не запускается
```bash
# Проверьте логи
sudo journalctl -u solarbalance-bot -n 50

# Проверьте конфигурацию
cat /home/solarbot/solarbalance/.env
```

### Проблемы с правами
```bash
# Исправьте права
sudo chown -R solarbot:solarbot /home/solarbot/solarbalance
```

### Проблемы с зависимостями
```bash
# Переустановите зависимости
sudo su - solarbot
cd /home/solarbot/solarbalance
source venv/bin/activate
pip install -r requirements-prod.txt --force-reinstall
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u solarbalance-bot -f`
2. Проверьте статус: `sudo systemctl status solarbalance-bot`
3. Проверьте конфигурацию в файле `.env`
4. Убедитесь, что все зависимости установлены

---

**Успешного деплоя! 🚀** 