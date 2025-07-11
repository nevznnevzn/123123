#!/bin/bash

# ==============================================
# SOLARBALANCE BOT - СКРИПТ ЗАПУСКА НА СЕРВЕРЕ
# ==============================================

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Запуск SolarBalance бота...${NC}"

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Виртуальное окружение не найдено!${NC}"
    echo -e "${YELLOW}Запустите сначала: ./deploy.sh${NC}"
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo -e "${YELLOW}Создайте .env файл с настройками бота${NC}"
    exit 1
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем зависимости
echo -e "${GREEN}🔍 Проверка зависимостей...${NC}"
python3 -c "
import sys
try:
    import aiogram
    import sqlalchemy
    import swisseph
    print('✅ Основные зависимости найдены')
except ImportError as e:
    print(f'❌ Отсутствует зависимость: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Не все зависимости установлены!${NC}"
    echo -e "${YELLOW}Запустите: ./deploy.sh${NC}"
    exit 1
fi

# Создаем необходимые директории
mkdir -p logs
mkdir -p assets
mkdir -p pics
mkdir -p pictures

echo -e "${GREEN}📁 Директории созданы${NC}"

# Проверяем конфигурацию
echo -e "${GREEN}⚙️ Проверка конфигурации...${NC}"
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

# Проверяем обязательные переменные
required_vars = ['BOT_TOKEN', 'ADMIN_IDS']
missing_vars = []

for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f'❌ Отсутствуют переменные: {missing_vars}')
    print('Отредактируйте .env файл')
    exit(1)
else:
    print('✅ Конфигурация корректна')
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка конфигурации!${NC}"
    exit 1
fi

# Запускаем бота
echo -e "${GREEN}🤖 Запуск бота...${NC}"
echo -e "${YELLOW}Для остановки нажмите Ctrl+C${NC}"
echo ""

# Запуск с обработкой ошибок
python3 main.py 