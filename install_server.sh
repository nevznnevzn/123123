#!/bin/bash

# 🚀 Скрипт автоматической установки Solar Balance Bot на сервер
# Использование: sudo bash install_server.sh

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка root прав
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Этот скрипт должен быть запущен с правами root (sudo)"
        exit 1
    fi
}

# Проверка ОС
check_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "Не удалось определить операционную систему"
        exit 1
    fi
    
    log_info "Обнаружена ОС: $OS $VER"
    
    # Проверяем поддержку
    if [[ "$OS" != *"Ubuntu"* ]] && [[ "$OS" != *"Debian"* ]]; then
        log_warning "Скрипт тестировался на Ubuntu/Debian. Другие ОС могут работать некорректно."
    fi
}

# Обновление системы
update_system() {
    log_info "Обновление системы..."
    apt update && apt upgrade -y
    log_success "Система обновлена"
}

# Установка зависимостей
install_dependencies() {
    log_info "Установка системных зависимостей..."
    
    # Основные пакеты
    apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
    apt install -y git curl wget build-essential libssl-dev libffi-dev
    
    # PostgreSQL (опционально)
    read -p "Установить PostgreSQL? (y/n): " install_postgres
    if [[ $install_postgres =~ ^[Yy]$ ]]; then
        apt install -y postgresql postgresql-contrib libpq-dev
        log_success "PostgreSQL установлен"
    fi
    
    log_success "Зависимости установлены"
}

# Создание пользователя
create_user() {
    log_info "Создание пользователя solarbot..."
    
    if id "solarbot" &>/dev/null; then
        log_warning "Пользователь solarbot уже существует"
    else
        useradd -m -s /bin/bash solarbot
        usermod -aG sudo solarbot
        log_success "Пользователь solarbot создан"
    fi
}

# Клонирование репозитория
clone_repository() {
    log_info "Клонирование репозитория..."
    
    # Запрашиваем URL репозитория
    read -p "Введите URL репозитория (или нажмите Enter для использования текущей директории): " repo_url
    
    if [[ -z "$repo_url" ]]; then
        # Используем текущую директорию
        if [[ -f "main.py" ]]; then
            log_info "Используем текущую директорию как репозиторий"
            cp -r . /home/solarbot/solarbalance
            chown -R solarbot:solarbot /home/solarbot/solarbalance
        else
            log_error "Файл main.py не найден в текущей директории"
            exit 1
        fi
    else
        # Клонируем репозиторий
        su - solarbot -c "cd /home/solarbot && git clone $repo_url solarbalance"
    fi
    
    log_success "Репозиторий готов"
}

# Настройка виртуального окружения
setup_venv() {
    log_info "Настройка виртуального окружения..."
    
    su - solarbot -c "cd /home/solarbot/solarbalance && python3.11 -m venv venv"
    su - solarbot -c "cd /home/solarbot/solarbalance && source venv/bin/activate && pip install --upgrade pip"
    
    # Устанавливаем зависимости
    if [[ -f "/home/solarbot/solarbalance/requirements-prod.txt" ]]; then
        su - solarbot -c "cd /home/solarbot/solarbalance && source venv/bin/activate && pip install -r requirements-prod.txt"
    elif [[ -f "/home/solarbot/solarbalance/requirements.txt" ]]; then
        su - solarbot -c "cd /home/solarbot/solarbalance && source venv/bin/activate && pip install -r requirements.txt"
    else
        log_warning "Файл requirements не найден, устанавливаем основные зависимости"
        su - solarbot -c "cd /home/solarbot/solarbalance && source venv/bin/activate && pip install aiogram apscheduler pytz sqlalchemy asyncpg aiosqlite openai"
    fi
    
    log_success "Виртуальное окружение настроено"
}

# Настройка конфигурации
setup_config() {
    log_info "Настройка конфигурации..."
    
    # Создаем .env файл
    if [[ ! -f "/home/solarbot/solarbalance/.env" ]]; then
        if [[ -f "/home/solarbot/solarbalance/env.example" ]]; then
            cp /home/solarbot/solarbalance/env.example /home/solarbot/solarbalance/.env
        else
            # Создаем базовый .env файл
            cat > /home/solarbot/solarbalance/.env << EOF
# Telegram Bot Token
BOT_TOKEN=your_bot_token_here

# Database (SQLite по умолчанию)
DATABASE_URL=sqlite+aiosqlite:///astro_bot.db

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://bothub.chat/api/v2/openai/v1

# Logging
LOG_LEVEL=INFO

# Environment
ENVIRONMENT=production
EOF
        fi
        chown solarbot:solarbot /home/solarbot/solarbalance/.env
        chmod 600 /home/solarbot/solarbalance/.env
    fi
    
    log_warning "Пожалуйста, отредактируйте файл /home/solarbot/solarbalance/.env и добавьте ваши API ключи"
    log_success "Конфигурация создана"
}

# Настройка systemd сервиса
setup_systemd() {
    log_info "Настройка systemd сервиса..."
    
    cat > /etc/systemd/system/solarbalance-bot.service << EOF
[Unit]
Description=Solar Balance Telegram Bot
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=solarbot
Group=solarbot
WorkingDirectory=/home/solarbot/solarbalance
Environment=PATH=/home/solarbot/solarbalance/venv/bin
ExecStart=/home/solarbot/solarbalance/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable solarbalance-bot
    
    log_success "Systemd сервис настроен"
}

# Настройка логов
setup_logs() {
    log_info "Настройка системы логирования..."
    
    mkdir -p /home/solarbot/solarbalance/logs
    chown -R solarbot:solarbot /home/solarbot/solarbalance/logs
    chmod 755 /home/solarbot/solarbalance/logs
    
    # Создаем ротацию логов
    cat > /etc/logrotate.d/solarbalance-bot << EOF
/home/solarbot/solarbalance/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 solarbot solarbot
    postrotate
        systemctl reload solarbalance-bot
    endscript
}
EOF
    
    log_success "Система логирования настроена"
}

# Создание скриптов управления
create_management_scripts() {
    log_info "Создание скриптов управления..."
    
    # Скрипт обновления
    cat > /home/solarbot/update_bot.sh << 'EOF'
#!/bin/bash
echo "🔄 Обновление Solar Balance Bot..."

# Останавливаем бота
sudo systemctl stop solarbalance-bot

# Переходим в директорию проекта
cd /home/solarbot/solarbalance

# Активируем venv
source venv/bin/activate

# Получаем обновления
git pull origin main

# Обновляем зависимости
pip install -r requirements-prod.txt --upgrade

# Запускаем бота
sudo systemctl start solarbalance-bot

echo "✅ Обновление завершено!"
echo "📊 Статус сервиса:"
sudo systemctl status solarbalance-bot --no-pager
EOF
    
    # Скрипт мониторинга
    cat > /home/solarbot/check_bot.sh << 'EOF'
#!/bin/bash
echo "📊 Solar Balance Bot Status"
echo "=========================="

# Статус сервиса
echo "🔧 Service Status:"
systemctl is-active solarbalance-bot

# Использование ресурсов
echo -e "\n💻 Resource Usage:"
ps aux | grep python | grep solarbalance | awk '{print "CPU: " $3 "%, RAM: " $4 "%, PID: " $2}'

# Размер логов
echo -e "\n📝 Log Files:"
du -sh /home/solarbot/solarbalance/logs/

# Последние ошибки
echo -e "\n❌ Recent Errors:"
journalctl -u solarbalance-bot --since "1 hour ago" | grep -i error | tail -5
EOF
    
    chmod +x /home/solarbot/update_bot.sh
    chmod +x /home/solarbot/check_bot.sh
    chown solarbot:solarbot /home/solarbot/update_bot.sh
    chown solarbot:solarbot /home/solarbot/check_bot.sh
    
    log_success "Скрипты управления созданы"
}

# Финальная настройка
final_setup() {
    log_info "Финальная настройка..."
    
    # Устанавливаем права на файлы
    chown -R solarbot:solarbot /home/solarbot/solarbalance
    
    # Создаем символические ссылки для удобства
    ln -sf /home/solarbot/update_bot.sh /usr/local/bin/update-solarbot
    ln -sf /home/solarbot/check_bot.sh /usr/local/bin/check-solarbot
    
    log_success "Финальная настройка завершена"
}

# Вывод инструкций
show_instructions() {
    echo ""
    echo "🎉 Установка завершена!"
    echo "========================"
    echo ""
    echo "📝 Следующие шаги:"
    echo "1. Отредактируйте конфигурацию:"
    echo "   sudo nano /home/solarbot/solarbalance/.env"
    echo ""
    echo "2. Добавьте ваши API ключи в .env файл:"
    echo "   - BOT_TOKEN (от @BotFather)"
    echo "   - OPENAI_API_KEY (от OpenAI или Bothub)"
    echo ""
    echo "3. Запустите бота:"
    echo "   sudo systemctl start solarbalance-bot"
    echo ""
    echo "4. Проверьте статус:"
    echo "   sudo systemctl status solarbalance-bot"
    echo ""
    echo "5. Просмотрите логи:"
    echo "   sudo journalctl -u solarbalance-bot -f"
    echo ""
    echo "🔧 Полезные команды:"
    echo "   update-solarbot    - Обновить бота"
    echo "   check-solarbot     - Проверить статус"
    echo "   sudo systemctl restart solarbalance-bot  - Перезапустить"
    echo "   sudo systemctl stop solarbalance-bot     - Остановить"
    echo ""
    echo "📁 Файлы:"
    echo "   Конфигурация: /home/solarbot/solarbalance/.env"
    echo "   Логи: /home/solarbot/solarbalance/logs/"
    echo "   Скрипты: /home/solarbot/update_bot.sh, /home/solarbot/check_bot.sh"
    echo ""
}

# Главная функция
main() {
    echo "🚀 Установка Solar Balance Bot на сервер"
    echo "========================================"
    echo ""
    
    check_root
    check_os
    update_system
    install_dependencies
    create_user
    clone_repository
    setup_venv
    setup_config
    setup_systemd
    setup_logs
    create_management_scripts
    final_setup
    show_instructions
}

# Запуск главной функции
main "$@" 