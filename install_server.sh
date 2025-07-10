#!/bin/bash

# 🚀 Автоматическая установка SolarBalance на сервер
# Использование: ./install_server.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для цветного вывода
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав суперпользователя
check_sudo() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт должен запускаться с правами root (sudo)"
        exit 1
    fi
}

# Определение ОС
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        print_error "Не удалось определить операционную систему"
        exit 1
    fi
    print_status "Обнаружена ОС: $OS $VER"
}

# Установка системных зависимостей
install_system_deps() {
    print_status "Установка системных зависимостей..."
    
    if [[ $OS == *"Ubuntu"* ]] || [[ $OS == *"Debian"* ]]; then
        apt update && apt upgrade -y
        apt install -y python3 python3-pip python3-venv git curl wget
        apt install -y build-essential python3-dev
        apt install -y postgresql-client
        apt install -y nano htop unzip
    elif [[ $OS == *"CentOS"* ]] || [[ $OS == *"Red Hat"* ]]; then
        yum update -y
        yum install -y python3 python3-pip python3-venv git curl wget
        yum groupinstall -y "Development Tools"
        yum install -y python3-devel
        yum install -y nano htop unzip
    else
        print_error "Неподдерживаемая операционная система: $OS"
        exit 1
    fi
    
    print_success "Системные зависимости установлены"
}

# Создание пользователя
create_user() {
    print_status "Создание пользователя solarbalance..."
    
    if id "solarbalance" &>/dev/null; then
        print_warning "Пользователь solarbalance уже существует"
    else
        useradd -m -s /bin/bash solarbalance
        print_success "Пользователь solarbalance создан"
    fi
}

# Установка UV
install_uv() {
    print_status "Установка UV (быстрый пакетный менеджер)..."
    
    su - solarbalance -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
    su - solarbalance -c "source ~/.bashrc"
    
    print_success "UV установлен"
}

# Клонирование репозитория
clone_repository() {
    print_status "Клонирование репозитория..."
    
    read -p "Введите URL вашего Git репозитория: " REPO_URL
    
    if [[ -z "$REPO_URL" ]]; then
        print_error "URL репозитория не может быть пустым"
        exit 1
    fi
    
    su - solarbalance -c "
        cd /home/solarbalance
        if [[ -d solarbalance-bot ]]; then
            rm -rf solarbalance-bot
        fi
        git clone $REPO_URL solarbalance-bot
    "
    
    print_success "Репозиторий клонирован"
}

# Настройка Python окружения
setup_python_env() {
    print_status "Настройка Python окружения..."
    
    su - solarbalance -c "
        cd /home/solarbalance/solarbalance-bot
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        
        # Устанавливаем зависимости
        if command -v uv &> /dev/null; then
            uv pip install -e .
        else
            pip install -e .
        fi
    "
    
    print_success "Python окружение настроено"
}

# Конфигурация
setup_config() {
    print_status "Настройка конфигурации..."
    
    su - solarbalance -c "
        cd /home/solarbalance/solarbalance-bot
        
        # Создаем директории
        mkdir -p logs assets
        chmod 755 logs assets
        
        # Копируем пример конфигурации
        cp env.example .env
        chmod 600 .env
    "
    
    print_warning "ВАЖНО: Не забудьте отредактировать файл .env!"
    print_warning "Путь к файлу: /home/solarbalance/solarbalance-bot/.env"
    print_warning "Обязательно укажите:"
    print_warning "  - BOT_TOKEN (получите у @BotFather)"
    print_warning "  - AI_API (ключ Bothub или OpenAI)"
    print_warning "  - ADMIN_IDS (ваш Telegram ID)"
    
    print_success "Базовая конфигурация создана"
}

# Создание systemd сервиса
create_systemd_service() {
    print_status "Создание systemd сервиса..."
    
    cat > /etc/systemd/system/solarbalance.service << 'EOF'
[Unit]
Description=SolarBalance Astrology Telegram Bot
After=network.target postgresql.service
Wants=network.target

[Service]
Type=simple
User=solarbalance
Group=solarbalance
WorkingDirectory=/home/solarbalance/solarbalance-bot
Environment=PATH=/home/solarbalance/solarbalance-bot/venv/bin
ExecStart=/home/solarbalance/solarbalance-bot/venv/bin/python main_simple.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/solarbalance/solarbalance-bot

# Логи
StandardOutput=append:/home/solarbalance/solarbalance-bot/logs/systemd.log
StandardError=append:/home/solarbalance/solarbalance-bot/logs/systemd.log

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable solarbalance
    
    print_success "Systemd сервис создан и включен"
}

# Настройка файрвола
setup_firewall() {
    print_status "Настройка файрвола..."
    
    if command -v ufw &> /dev/null; then
        ufw --force enable
        ufw allow ssh
        print_success "Файрвол настроен"
    else
        print_warning "UFW не установлен, пропускаем настройку файрвола"
    fi
}

# Создание вспомогательных скриптов
create_helper_scripts() {
    print_status "Создание вспомогательных скриптов..."
    
    # Скрипт обновления
    cat > /home/solarbalance/solarbalance-bot/update_bot.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 Обновление SolarBalance..."

# Останавливаем бота
sudo systemctl stop solarbalance

# Переходим в директорию проекта
cd /home/solarbalance/solarbalance-bot

# Активируем venv
source venv/bin/activate

# Получаем обновления
git pull origin main

# Обновляем зависимости
if command -v uv &> /dev/null; then
    uv pip install -e .
else
    pip install -e .
fi

# Проверяем миграции БД (если есть)
python -c "from database_async import async_db_manager; import asyncio; asyncio.run(async_db_manager.init_db())" || true

# Запускаем бота
sudo systemctl start solarbalance

echo "✅ Обновление завершено!"
echo "📊 Статус сервиса:"
sudo systemctl status solarbalance --no-pager
EOF

    # Скрипт мониторинга
    cat > /home/solarbalance/solarbalance-bot/monitor.sh << 'EOF'
#!/bin/bash

echo "📊 SolarBalance Bot Status"
echo "========================="

# Статус сервиса
echo "🔧 Service Status:"
systemctl is-active solarbalance || echo "inactive"

# Использование ресурсов
echo -e "\n💻 Resource Usage:"
ps aux | grep python | grep solarbalance | awk '{print "CPU: " $3 "%, RAM: " $4 "%, PID: " $2}' || echo "Process not found"

# Размер логов
echo -e "\n📝 Log Files:"
du -sh logs/ 2>/dev/null || echo "No logs directory"

# Размер БД
echo -e "\n🗄️ Database:"
if [ -f "solarbalance.db" ]; then
    du -sh solarbalance.db
else
    echo "Database file not found"
fi

# Последние ошибки
echo -e "\n❌ Recent Errors:"
journalctl -u solarbalance --since "1 hour ago" 2>/dev/null | grep -i error | tail -5 || echo "No recent errors"
EOF

    # Делаем скрипты исполняемыми
    chmod +x /home/solarbalance/solarbalance-bot/update_bot.sh
    chmod +x /home/solarbalance/solarbalance-bot/monitor.sh
    chown solarbalance:solarbalance /home/solarbalance/solarbalance-bot/update_bot.sh
    chown solarbalance:solarbalance /home/solarbalance/solarbalance-bot/monitor.sh
    
    print_success "Вспомогательные скрипты созданы"
}

# Финальная проверка
final_check() {
    print_status "Проведение финальной проверки..."
    
    # Проверяем, что все файлы на месте
    if [[ ! -f /home/solarbalance/solarbalance-bot/main_simple.py ]]; then
        print_error "Файл main_simple.py не найден!"
        exit 1
    fi
    
    if [[ ! -f /home/solarbalance/solarbalance-bot/.env ]]; then
        print_error "Файл .env не найден!"
        exit 1
    fi
    
    print_success "Все файлы на месте"
}

# Главная функция
main() {
    echo -e "${BLUE}"
    echo "🚀 Автоматическая установка SolarBalance"
    echo "========================================"
    echo -e "${NC}"
    
    check_sudo
    detect_os
    install_system_deps
    create_user
    install_uv
    clone_repository
    setup_python_env
    setup_config
    create_systemd_service
    setup_firewall
    create_helper_scripts
    final_check
    
    echo -e "${GREEN}"
    echo "✅ Установка завершена успешно!"
    echo "==============================="
    echo -e "${NC}"
    
    print_warning "СЛЕДУЮЩИЕ ШАГИ:"
    echo "1. Отредактируйте файл конфигурации:"
    echo "   nano /home/solarbalance/solarbalance-bot/.env"
    echo ""
    echo "2. Запустите бота:"
    echo "   systemctl start solarbalance"
    echo ""
    echo "3. Проверьте статус:"
    echo "   systemctl status solarbalance"
    echo ""
    echo "4. Посмотрите логи:"
    echo "   journalctl -u solarbalance -f"
    echo ""
    echo "📚 Полная документация: deploy_server.md"
    echo "🔧 Скрипт мониторинга: /home/solarbalance/solarbalance-bot/monitor.sh"
    echo "🔄 Скрипт обновления: /home/solarbalance/solarbalance-bot/update_bot.sh"
}

# Запуск
main "$@" 