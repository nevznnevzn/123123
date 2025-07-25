# 🚀 Краткая сводка по деплою Solar Balance Bot

## 📋 Что подготовлено

✅ **Автоматические скрипты:**
- `install_server.sh` - Полная автоматическая установка
- `quick_deploy.sh` - Быстрый деплой для опытных пользователей
- `update_existing.sh` - Обновление существующей установки

✅ **Документация:**
- `DEPLOY_GUIDE.md` - Полное руководство по деплою
- `deploy_server.md` - Детальные инструкции
- `README_DEPLOY.md` - Краткое README

✅ **Конфигурация:**
- `requirements-prod.txt` - Зависимости для продакшена
- `env.example` - Пример конфигурации

## 🚀 Быстрый старт (4 варианта)

### 1. Автоматическая установка (рекомендуется)
```bash
# На сервере
sudo bash install_server.sh
```

### 2. Обновление существующей установки
```bash
# Если бот уже установлен
sudo bash update_existing.sh
```

### 3. Быстрый деплой
```bash
# На сервере
sudo bash quick_deploy.sh
```

### 4. Ручная установка
Следуйте `deploy_server.md`

## ⚙️ После установки

1. **Настройте конфигурацию:**
   ```bash
   sudo nano /home/solarbot/solarbalance/.env
   ```

2. **Добавьте API ключи:**
   ```env
   BOT_TOKEN=your_bot_token_from_botfather
   OPENAI_API_KEY=your_openai_api_key
   ```

3. **Запустите бота:**
   ```bash
   sudo systemctl start solarbalance-bot
   sudo systemctl status solarbalance-bot
   ```

## 🔧 Управление

```bash
# Основные команды
sudo systemctl start/stop/restart solarbalance-bot
sudo systemctl status solarbalance-bot
sudo journalctl -u solarbalance-bot -f

# Мониторинг
check-solarbot
update-solarbot
```

## 🛡️ Безопасность

- ✅ Отдельный пользователь `solarbot`
- ✅ Защищенные права на конфигурацию (600)
- ✅ Автоматическая ротация логов
- ✅ Systemd автоперезапуск

## 📊 Мониторинг

- Логи: `sudo journalctl -u solarbalance-bot -f`
- Статус: `sudo systemctl status solarbalance-bot`
- Проверка: `check-solarbot`

## 🔄 Обновление

```bash
# Автоматически
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
sudo journalctl -u solarbalance-bot -n 50
cat /home/solarbot/solarbalance/.env
```

### Проблемы с зависимостями
```bash
sudo su - solarbot
cd /home/solarbot/solarbalance
source venv/bin/activate
pip install -r requirements-prod.txt --force-reinstall
```

## 📁 Структура после установки

```
/home/solarbot/solarbalance/
├── main.py                 # Главный файл бота
├── .env                    # Конфигурация (защищен)
├── venv/                   # Виртуальное окружение
├── logs/                   # Логи приложения
├── requirements-prod.txt   # Зависимости
└── ...

/etc/systemd/system/solarbalance-bot.service  # Systemd сервис
```

## ✅ Чек-лист

- [ ] Сервер Ubuntu 20.04+/Debian 11+
- [ ] Токен бота от @BotFather
- [ ] API ключ Bothub/OpenAI
- [ ] Запущена автоматическая установка
- [ ] Настроен файл `.env`
- [ ] Запущен сервис `solarbalance-bot`
- [ ] Проверена работа в Telegram
- [ ] Настроен файрвол

---

**🎉 Готово к деплою! 🚀** 