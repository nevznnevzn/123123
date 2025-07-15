#!/bin/bash

# ==============================================
# SOLARBALANCE - ИСПРАВЛЕНИЕ КОНФИГУРАЦИИ СЕРВЕРА
# ==============================================

echo "🔧 Исправление конфигурации SolarBalance на сервере..."
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/opt/solarbalance"

# Проверка, что скрипт запущен на сервере
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Ошибка: Директория $PROJECT_DIR не найдена!${NC}"
    echo "Этот скрипт должен быть запущен на сервере где установлен SolarBalance"
    exit 1
fi

cd "$PROJECT_DIR"

echo -e "${BLUE}📁 Рабочая директория: $(pwd)${NC}"
echo ""

# 1. Исправление прав доступа к файлам
echo -e "${YELLOW}🔐 1. Исправление прав доступа...${NC}"

# Исправляем права на исполняемые файлы
chmod +x start_server.sh
chmod +x deploy.sh
echo -e "${GREEN}✅ Права на скрипты исправлены${NC}"

# 2. Проверка и создание .env файла
echo -e "${YELLOW}📝 2. Проверка конфигурации .env...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo "Создаем .env из env.example..."
    
    if [ -f "env.example" ]; then
        cp env.example .env
        echo -e "${GREEN}✅ Файл .env создан из env.example${NC}"
    else
        echo -e "${RED}❌ Файл env.example тоже не найден!${NC}"
        echo "Создаем базовый .env файл..."
        
        cat > .env << 'EOF'
# ==============================================
# SOLARBALANCE BOT - ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# ==============================================

# Telegram Bot
BOT_TOKEN=REPLACE_WITH_YOUR_BOT_TOKEN
TELEGRAM_BOT_TOKEN=REPLACE_WITH_YOUR_BOT_TOKEN

# Администраторы (ID через запятую)
ADMIN_IDS=123456789

# AI Service (для прогнозов)
AI_API=your_bothub_api_key_here
YANDEX_API_KEY=your_yandex_api_key_here

# База данных
DATABASE_URL=sqlite:///astro_bot.db

# Режим работы
ENVIRONMENT=production

# Логирование
LOG_LEVEL=INFO

# Безопасность
SECRET_KEY=generated_secret_key_$(date +%s)_$(openssl rand -hex 16)
EOF
        echo -e "${GREEN}✅ Базовый .env файл создан${NC}"
    fi
else
    echo -e "${GREEN}✅ Файл .env уже существует${NC}"
fi

# Исправляем права доступа к .env
chmod 600 .env
echo -e "${GREEN}✅ Права доступа к .env исправлены (600)${NC}"

# 3. Проверка токена бота
echo ""
echo -e "${YELLOW}🤖 3. Проверка токена Telegram бота...${NC}"

BOT_TOKEN=$(grep "^BOT_TOKEN=" .env | cut -d'=' -f2)

if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" = "your_telegram_bot_token_here" ] || [ "$BOT_TOKEN" = "REPLACE_WITH_YOUR_BOT_TOKEN" ]; then
    echo -e "${RED}❌ Токен бота не установлен или использует значение по умолчанию!${NC}"
    echo ""
    echo -e "${BLUE}📋 Инструкции по получению токена:${NC}"
    echo "1. Откройте Telegram и найдите @BotFather"
    echo "2. Отправьте команду /newbot (для создания нового бота)"
    echo "   ИЛИ /token (если бот уже существует)"
    echo "3. Следуйте инструкциям BotFather"
    echo "4. Скопируйте полученный токен"
    echo ""
    echo -e "${YELLOW}⚠️  Токен должен выглядеть примерно так: 123456789:AABCDefGhIJKlmNOPqrsTUVwxyZ${NC}"
    echo ""
    
    read -p "🔑 Введите токен вашего Telegram бота: " USER_TOKEN
    
    if [ -n "$USER_TOKEN" ]; then
        # Обновляем токен в .env файле
        sed -i "s/^BOT_TOKEN=.*/BOT_TOKEN=$USER_TOKEN/" .env
        sed -i "s/^TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=$USER_TOKEN/" .env
        echo -e "${GREEN}✅ Токен бота обновлен в .env файле${NC}"
    else
        echo -e "${RED}❌ Токен не введен. Нужно будет настроить вручную!${NC}"
    fi
else
    echo -e "${GREEN}✅ Токен бота настроен${NC}"
fi

# 4. Проверка администраторов
echo ""
echo -e "${YELLOW}👥 4. Проверка ID администраторов...${NC}"

ADMIN_IDS=$(grep "^ADMIN_IDS=" .env | cut -d'=' -f2)

if [ -z "$ADMIN_IDS" ] || [ "$ADMIN_IDS" = "123456789" ]; then
    echo -e "${YELLOW}⚠️  ID администраторов не настроены или используют значение по умолчанию${NC}"
    echo ""
    echo -e "${BLUE}📋 Как узнать свой Telegram ID:${NC}"
    echo "1. Напишите боту @userinfobot в Telegram"
    echo "2. Отправьте ему любое сообщение"
    echo "3. Он ответит с вашим ID"
    echo ""
    
    read -p "👤 Введите ваш Telegram ID (или оставьте пустым для настройки позже): " USER_ID
    
    if [ -n "$USER_ID" ]; then
        sed -i "s/^ADMIN_IDS=.*/ADMIN_IDS=$USER_ID/" .env
        echo -e "${GREEN}✅ ID администратора обновлен${NC}"
    else
        echo -e "${YELLOW}⚠️  ID администратора не изменен${NC}"
    fi
else
    echo -e "${GREEN}✅ ID администраторов настроены: $ADMIN_IDS${NC}"
fi

# 5. Генерация нового SECRET_KEY если нужно
echo ""
echo -e "${YELLOW}🔐 5. Проверка SECRET_KEY...${NC}"

SECRET_KEY=$(grep "^SECRET_KEY=" .env | cut -d'=' -f2)

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your_secret_key_here" ]; then
    NEW_SECRET=$(openssl rand -hex 32)
    sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
    echo -e "${GREEN}✅ Новый SECRET_KEY сгенерирован${NC}"
else
    echo -e "${GREEN}✅ SECRET_KEY уже настроен${NC}"
fi

# 6. Остановка и перезапуск сервиса
echo ""
echo -e "${YELLOW}🔄 6. Перезапуск сервиса...${NC}"

echo "Останавливаем сервис..."
sudo systemctl stop solarbalance 2>/dev/null || true

sleep 2

echo "Запускаем сервис..."
sudo systemctl start solarbalance

sleep 3

echo "Проверяем статус сервиса..."
if sudo systemctl is-active --quiet solarbalance; then
    echo -e "${GREEN}✅ Сервис успешно запущен!${NC}"
else
    echo -e "${RED}❌ Сервис не запустился. Проверяем логи...${NC}"
    echo ""
    echo -e "${BLUE}📋 Последние логи сервиса:${NC}"
    sudo journalctl -u solarbalance -n 10 --no-pager
fi

# 7. Итоговая проверка
echo ""
echo -e "${BLUE}🔍 7. Итоговая проверка конфигурации...${NC}"

# Проверяем текущую конфигурацию
echo ""
echo -e "${BLUE}📊 Текущая конфигурация:${NC}"
echo "$(grep "^BOT_TOKEN=" .env | sed 's/BOT_TOKEN=\(.\{10\}\).*/BOT_TOKEN=\1.../' )"
echo "$(grep "^ADMIN_IDS=" .env)"
echo "$(grep "^DATABASE_URL=" .env)"
echo "$(grep "^ENVIRONMENT=" .env)"

echo ""
echo -e "${GREEN}🎉 Конфигурация обновлена!${NC}"
echo ""

# Показываем полезные команды
echo -e "${BLUE}📋 Полезные команды для управления ботом:${NC}"
echo ""
echo "Проверить статус:     sudo systemctl status solarbalance"
echo "Остановить бота:      sudo systemctl stop solarbalance"
echo "Запустить бота:       sudo systemctl start solarbalance"
echo "Перезапустить бота:   sudo systemctl restart solarbalance"
echo "Посмотреть логи:      sudo journalctl -u solarbalance -f"
echo "Последние 20 строк:   sudo journalctl -u solarbalance -n 20"
echo ""

echo -e "${YELLOW}⚠️  ВАЖНО:${NC}"
echo "1. Убедитесь, что токен бота корректный"
echo "2. Проверьте, что бот не используется в другом месте"
echo "3. Если проблемы продолжаются, запустите: sudo journalctl -u solarbalance -f"
echo ""

echo -e "${GREEN}✅ Готово! Проверьте работу бота в Telegram.${NC}" 