# 🔄 Обновление существующей установки Solar Balance Bot

## 📋 Когда использовать

Используйте этот скрипт, если:
- ✅ Бот уже установлен на сервере
- ✅ Нужно обновить код до новой версии
- ✅ Хотите сохранить существующие данные и конфигурацию

## 🚀 Быстрое обновление

### Автоматическое обновление (рекомендуется)
```bash
# Загрузите новую версию на сервер
git clone <your-repo-url> /tmp/solarbalance-new
cd /tmp/solarbalance-new

# Запустите скрипт обновления
sudo bash update_existing.sh
```

### Что делает скрипт:
1. 🔍 **Находит существующую установку** в стандартных директориях
2. 💾 **Создает резервную копию** важных файлов (.env, база данных, логи)
3. ⏹️ **Останавливает сервис** бота
4. 📝 **Обновляет код** (через git или копирование файлов)
5. 📦 **Обновляет зависимости** в виртуальном окружении
6. ⚙️ **Обновляет systemd сервис**
7. ▶️ **Запускает сервис** и проверяет работоспособность

## 🔧 Ручное обновление

### 1. Резервное копирование
```bash
# Создаем резервную копию
sudo cp /home/solarbot/solarbalance/.env /tmp/solarbalance_backup.env
sudo cp /home/solarbot/solarbalance/astro_bot.db /tmp/solarbalance_backup.db
```

### 2. Остановка сервиса
```bash
sudo systemctl stop solarbalance-bot
```

### 3. Обновление кода
```bash
cd /home/solarbot/solarbalance

# Если это git репозиторий
git fetch origin
git reset --hard origin/main

# Или копируем новые файлы вручную
# (замените на путь к новым файлам)
cp -r /path/to/new/files/* .
```

### 4. Обновление зависимостей
```bash
source venv/bin/activate
pip install -r requirements-prod.txt --upgrade
```

### 5. Запуск сервиса
```bash
sudo systemctl start solarbalance-bot
sudo systemctl status solarbalance-bot
```

## 🛡️ Безопасность

### Автоматическое резервное копирование
Скрипт `update_existing.sh` автоматически создает резервную копию:
- 📁 `.env` файл с конфигурацией
- 🗄️ База данных SQLite
- 📝 Логи приложения

Резервная копия сохраняется в `/tmp/solarbalance_backup_YYYYMMDD_HHMMSS.tar.gz`

### Восстановление из резервной копии
```bash
# Распаковка резервной копии
tar -xzf /tmp/solarbalance_backup_YYYYMMDD_HHMMSS.tar.gz -C /tmp

# Восстановление файлов
sudo cp /tmp/solarbalance_backup/.env /home/solarbot/solarbalance/
sudo cp /tmp/solarbalance_backup/astro_bot.db /home/solarbot/solarbalance/
sudo cp -r /tmp/solarbalance_backup/logs /home/solarbot/solarbalance/

# Установка правильных прав
sudo chown -R solarbot:solarbot /home/solarbot/solarbalance/
sudo chmod 600 /home/solarbot/solarbalance/.env
```

## 🔍 Поиск существующих установок

Скрипт автоматически ищет установки в следующих директориях:
- `/home/solarbot/solarbalance`
- `/home/solarbalance/solarbalance`
- `/home/solarbalance/solarbalance-bot`
- `/opt/solarbalance`
- `/var/www/solarbalance`

Если установка не найдена, можно указать путь вручную.

## ⚠️ Важные моменты

### Перед обновлением:
- ✅ Убедитесь, что у вас есть доступ к серверу
- ✅ Проверьте, что бот работает стабильно
- ✅ Создайте резервную копию вручную (на всякий случай)

### После обновления:
- ✅ Проверьте статус сервиса: `sudo systemctl status solarbalance-bot`
- ✅ Проверьте логи: `sudo journalctl -u solarbalance-bot -f`
- ✅ Протестируйте бота в Telegram
- ✅ Проверьте работу основных функций

### Если что-то пошло не так:
1. **Остановите сервис:** `sudo systemctl stop solarbalance-bot`
2. **Восстановите из резервной копии** (см. выше)
3. **Проверьте логи:** `sudo journalctl -u solarbalance-bot -n 50`
4. **При необходимости откатитесь к предыдущей версии**

## 📊 Мониторинг после обновления

```bash
# Проверка статуса
sudo systemctl status solarbalance-bot

# Просмотр логов
sudo journalctl -u solarbalance-bot -f

# Проверка процесса
ps aux | grep python | grep main.py

# Проверка ошибок
sudo journalctl -u solarbalance-bot --since "10 minutes ago" | grep -i error
```

## 🔄 Частые сценарии обновления

### Обновление через Git
```bash
cd /home/solarbot/solarbalance
git fetch origin
git reset --hard origin/main
source venv/bin/activate
pip install -r requirements-prod.txt --upgrade
sudo systemctl restart solarbalance-bot
```

### Обновление файлов вручную
```bash
# Остановка
sudo systemctl stop solarbalance-bot

# Копирование новых файлов
sudo cp -r /path/to/new/files/* /home/solarbot/solarbalance/

# Обновление зависимостей
cd /home/solarbot/solarbalance
source venv/bin/activate
pip install -r requirements-prod.txt --upgrade

# Запуск
sudo systemctl start solarbalance-bot
```

---

**🔄 Успешного обновления! 🚀** 