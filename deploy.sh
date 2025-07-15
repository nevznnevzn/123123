#!/bin/bash

# ==============================================
# SOLARBALANCE BOT - СКРИПТ ДЕПЛОЯ НА СЕРВЕР
# ==============================================

set -e  # Остановка при ошибке

echo "🚀 Начинаем деплой SolarBalance бота..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода цветного текста
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка Python версии
check_python() {
    print_status "Проверка Python..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 не найден. Установите Python 3.9 или выше."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Найден Python $PYTHON_VERSION"
    
    # Проверка минимальной версии
    if false; then
        print_error "Требуется Python 3.9 или выше. Текущая версия: $PYTHON_VERSION"
        exit 1
    fi
}

# Установка системных зависимостей
install_system_deps() {
    print_status "Установка системных зависимостей..."
    
    # Определяем операционную систему
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Ubuntu/Debian
        if command -v apt-get &> /dev/null; then
            print_status "Обновляем пакеты Ubuntu/Debian..."
            sudo apt-get update
            sudo apt-get install -y python3-pip python3-venv python3-dev build-essential
            sudo apt-get install -y libffi-dev libssl-dev
            print_status "Системные зависимости установлены"
        # CentOS/RHEL
        elif command -v yum &> /dev/null; then
            print_status "Обновляем пакеты CentOS/RHEL..."
            sudo yum update -y
            sudo yum install -y python3-pip python3-devel gcc openssl-devel libffi-devel
            print_status "Системные зависимости установлены"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        print_status "Обнаружен macOS"
        if command -v brew &> /dev/null; then
            brew install python3
            print_status "Python3 установлен через Homebrew"
        else
            print_warning "Homebrew не найден. Установите его для упрощения установки зависимостей."
        fi
    fi
}

# Создание виртуального окружения
setup_venv() {
    print_status "Настройка виртуального окружения..."
    
    # Удаляем старое окружение если существует
    if [ -d "venv" ]; then
        print_warning "Удаляем старое виртуальное окружение..."
        rm -rf venv
    fi
    
    # Создаем новое окружение
    python3 -m venv venv
    print_status "Виртуальное окружение создано"
    
    # Активируем окружение
    source venv/bin/activate
    print_status "Виртуальное окружение активировано"
    
    # Обновляем pip
    pip install --upgrade pip setuptools wheel
    print_status "pip обновлен"
}

# Установка зависимостей
install_dependencies() {
    print_status "Установка зависимостей..."
    
    # Активируем окружение
    source venv/bin/activate
    
    # Устанавливаем зависимости
    if [ -f "requirements-prod.txt" ]; then
        pip install -r requirements-prod.txt
        print_status "Продакшен зависимости установлены"
    else
        print_error "Файл requirements-prod.txt не найден"
        exit 1
    fi
}

# Настройка конфигурации
setup_config() {
    print_status "Настройка конфигурации..."
    
    # Проверяем наличие .env файла
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            cp env.example .env
            print_warning "Создан .env файл из примера. ОБЯЗАТЕЛЬНО отредактируйте его!"
            print_warning "Файл .env содержит важные настройки бота."
        else
            print_error "Файл env.example не найден"
            exit 1
        fi
    else
        print_status ".env файл уже существует"
    fi
}

# Создание директорий
create_directories() {
    print_status "Создание необходимых директорий..."
    
    mkdir -p logs
    mkdir -p assets
    mkdir -p pics
    mkdir -p pictures
    
    print_status "Директории созданы"
}

# Проверка файлов эфемерид
check_ephemeris() {
    print_status "Проверка файлов эфемерид Swiss Ephemeris..."
    
    # Проверяем наличие файлов эфемерид
    if ls *.bsp 1> /dev/null 2>&1; then
        print_status "Файлы эфемерид найдены"
    else
        print_warning "Файлы эфемерид Swiss Ephemeris не найдены"
        print_warning "Скачайте файлы эфемерид с https://www.astro.com/swisseph/ephe/"
        print_warning "Рекомендуется скачать: de421.bsp, de422.bsp"
    fi
}

# Проверка конфигурации
validate_config() {
    print_status "Проверка конфигурации..."
    
    source venv/bin/activate
    
    # Проверяем импорты
    if python3 -c "import config; print('Config OK')" 2>/dev/null; then
        print_status "Конфигурация корректна"
    else
        print_error "Ошибка в конфигурации"
        exit 1
    fi
    
    # Проверяем обязательные переменные
    if python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['BOT_TOKEN', 'ADMIN_IDS']
missing_vars = []

for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f'Отсутствуют обязательные переменные: {missing_vars}')
    exit(1)
else:
    print('Все обязательные переменные настроены')
"; then
        print_status "Переменные окружения настроены корректно"
    else
        print_error "Отсутствуют обязательные переменные окружения"
        print_error "Отредактируйте .env файл и укажите все необходимые значения"
        exit 1
    fi
}

# Создание systemd сервиса
create_systemd_service() {
    print_status "Создание systemd сервиса..."
    
    CURRENT_DIR=$(pwd)
    USER=$(whoami)
    
    cat > solarbalance.service << EOF
[Unit]
Description=SolarBalance Astrology Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    print_status "Файл systemd сервиса создан: solarbalance.service"
    print_warning "Для установки сервиса выполните:"
    print_warning "sudo cp solarbalance.service /etc/systemd/system/"
    print_warning "sudo systemctl daemon-reload"
    print_warning "sudo systemctl enable solarbalance"
    print_warning "sudo systemctl start solarbalance"
}

# Тестирование
test_bot() {
    print_status "Тестирование бота..."
    
    source venv/bin/activate
    
    # Быстрый тест импортов
    if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from config import Config
    from database import DatabaseManager
    from main import main
    print('✅ Все модули импортируются корректно')
except Exception as e:
    print(f'❌ Ошибка импорта: {e}')
    sys.exit(1)
"; then
        print_status "Тест импортов пройден"
    else
        print_error "Тест импортов не пройден"
        exit 1
    fi
}

# Основная функция
main() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  SOLARBALANCE BOT DEPLOYMENT   ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    
    check_python
    install_system_deps
    setup_venv
    install_dependencies
    setup_config
    create_directories
    check_ephemeris
    validate_config
    create_systemd_service
    test_bot
    
    echo ""
    echo -e "${GREEN}🎉 Деплой завершен успешно!${NC}"
    echo ""
    echo -e "${YELLOW}Следующие шаги:${NC}"
    echo "1. Отредактируйте .env файл с вашими настройками"
    echo "2. Скачайте файлы эфемерид Swiss Ephemeris (*.bsp)"
    echo "3. Установите systemd сервис (команды выше)"
    echo "4. Запустите бота: sudo systemctl start solarbalance"
    echo "5. Проверьте статус: sudo systemctl status solarbalance"
    echo ""
    echo -e "${BLUE}Для ручного запуска:${NC}"
    echo "source venv/bin/activate && python main.py"
    echo ""
    echo -e "${GREEN}Удачного деплоя! 🚀${NC}"
}

# Запуск основной функции
main "$@" 