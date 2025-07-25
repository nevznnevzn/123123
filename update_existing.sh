#!/bin/bash

# 🔄 Скрипт обновления существующей установки Solar Balance Bot
# Использование: sudo bash update_existing.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Поиск существующей установки
find_existing_installation() {
    log_info "Поиск существующей установки..."
    
    # Возможные пути установки
    possible_paths=(
        "/home/solarbot/solarbalance"
        "/home/solarbalance/solarbalance"
        "/home/solarbalance/solarbalance-bot"
        "/opt/solarbalance"
        "/var/www/solarbalance"
    )
    
    for path in "${possible_paths[@]}"; do
        if [[ -d "$path" && -f "$path/main.py" ]]; then
            log_success "Найдена установка в: $path"
            return 0
        fi
    done
    
    log_error "Существующая установка не найдена!"
    log_info "Возможные причины:"
    log_info "1. Бот установлен в другой директории"
    log_info "2. Бот не был установлен ранее"
    log_info "3. Файл main.py отсутствует"
    
    read -p "Введите путь к существующей установке (или нажмите Enter для новой установки): " custom_path
    
    if [[ -n "$custom_path" && -d "$custom_path" && -f "$custom_path/main.py" ]]; then
        log_success "Найдена установка в: $custom_path"
        return 0
    elif [[ -z "$custom_path" ]]; then
        log_info "Запускаем новую установку..."
        exec bash install_server.sh
    else
        log_error "Указанный путь не содержит валидную установку бота"
        exit 1
    fi
}

# Резервное копирование
create_backup() {
    local install_path="$1"
    local backup_dir="/tmp/solarbalance_backup_$(date +%Y%m%d_%H%M%S)"
    
    log_info "Создание резервной копии..."
    
    mkdir -p "$backup_dir"
    
    # Копируем важные файлы
    if [[ -f "$install_path/.env" ]]; then
        cp "$install_path/.env" "$backup_dir/"
        log_info "Сохранен .env файл"
    fi
    
    if [[ -f "$install_path/astro_bot.db" ]]; then
        cp "$install_path/astro_bot.db" "$backup_dir/"
        log_info "Сохранена база данных"
    fi
    
    if [[ -d "$install_path/logs" ]]; then
        cp -r "$install_path/logs" "$backup_dir/"
        log_info "Сохранены логи"
    fi
    
    # Создаем архив
    tar -czf "${backup_dir}.tar.gz" -C /tmp "$(basename "$backup_dir")"
    rm -rf "$backup_dir"
    
    log_success "Резервная копия создана: ${backup_dir}.tar.gz"
}

# Остановка сервиса
stop_service() {
    log_info "Остановка сервиса..."
    
    # Проверяем разные имена сервисов
    service_names=("solarbalance-bot" "solarbalance" "solarbot")
    
    for service in "${service_names[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            log_info "Останавливаем сервис: $service"
            systemctl stop "$service"
            break
        fi
    done
    
    # Проверяем процессы Python
    pids=$(pgrep -f "python.*main.py" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        log_info "Завершение процессов Python..."
        kill $pids 2>/dev/null || true
        sleep 2
    fi
}

# Обновление кода
update_code() {
    local install_path="$1"
    
    log_info "Обновление кода..."
    
    # Определяем пользователя
    local user=$(stat -c '%U' "$install_path")
    local group=$(stat -c '%G' "$install_path")
    
    log_info "Пользователь: $user, группа: $group"
    
    # Если это git репозиторий
    if [[ -d "$install_path/.git" ]]; then
        log_info "Обнаружен git репозиторий, обновляем через git..."
        su - "$user" -c "cd '$install_path' && git fetch origin && git reset --hard origin/main"
    else
        log_info "Копируем новые файлы..."
        
        # Создаем временную директорию
        local temp_dir="/tmp/solarbalance_update_$(date +%s)"
        mkdir -p "$temp_dir"
        
        # Копируем текущую директорию (новые файлы)
        cp -r . "$temp_dir/"
        
        # Удаляем старые файлы (кроме важных)
        cd "$install_path"
        find . -type f \( -name "*.py" -o -name "*.sh" -o -name "*.md" -o -name "requirements*.txt" \) -delete
        find . -type d \( -name "handlers" -o -name "services" -o -name "tests" \) -exec rm -rf {} + 2>/dev/null || true
        
        # Копируем новые файлы
        cp -r "$temp_dir"/* .
        
        # Очищаем временную директорию
        rm -rf "$temp_dir"
    fi
    
    # Устанавливаем правильные права
    chown -R "$user:$group" "$install_path"
}

# Обновление зависимостей
update_dependencies() {
    local install_path="$1"
    local user=$(stat -c '%U' "$install_path")
    
    log_info "Обновление зависимостей..."
    
    # Активируем venv и обновляем зависимости
    su - "$user" -c "cd '$install_path' && source venv/bin/activate && pip install --upgrade pip"
    
    if [[ -f "$install_path/requirements-prod.txt" ]]; then
        su - "$user" -c "cd '$install_path' && source venv/bin/activate && pip install -r requirements-prod.txt --upgrade"
    elif [[ -f "$install_path/requirements.txt" ]]; then
        su - "$user" -c "cd '$install_path' && source venv/bin/activate && pip install -r requirements.txt --upgrade"
    else
        log_warning "Файл requirements не найден, устанавливаем основные зависимости"
        su - "$user" -c "cd '$install_path' && source venv/bin/activate && pip install aiogram apscheduler pytz sqlalchemy asyncpg aiosqlite openai python-dotenv pyswisseph --upgrade"
    fi
    
    log_success "Зависимости обновлены"
}

# Обновление systemd сервиса
update_systemd_service() {
    log_info "Обновление systemd сервиса..."
    
    # Определяем имя сервиса
    local service_name="solarbalance-bot"
    local install_path="$1"
    local user=$(stat -c '%U' "$install_path")
    
    # Создаем новый файл сервиса
    cat > /etc/systemd/system/solarbalance-bot.service << EOF
[Unit]
Description=Solar Balance Telegram Bot
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=$user
Group=$user
WorkingDirectory=$install_path
Environment=PATH=$install_path/venv/bin
ExecStart=$install_path/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable solarbalance-bot
    
    log_success "Systemd сервис обновлен"
}

# Проверка конфигурации
check_configuration() {
    local install_path="$1"
    
    log_info "Проверка конфигурации..."
    
    if [[ ! -f "$install_path/.env" ]]; then
        log_warning "Файл .env не найден, создаем базовый..."
        
        cat > "$install_path/.env" << EOF
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
        
        local user=$(stat -c '%U' "$install_path")
        chown "$user:$user" "$install_path/.env"
        chmod 600 "$install_path/.env"
        
        log_warning "Создан базовый .env файл. Пожалуйста, отредактируйте его!"
    else
        log_success "Конфигурация найдена"
    fi
}

# Запуск сервиса
start_service() {
    log_info "Запуск сервиса..."
    
    systemctl start solarbalance-bot
    
    # Ждем немного и проверяем статус
    sleep 3
    
    if systemctl is-active --quiet solarbalance-bot; then
        log_success "Сервис успешно запущен!"
        log_info "Статус: $(systemctl is-active solarbalance-bot)"
    else
        log_error "Ошибка запуска сервиса!"
        log_info "Проверьте логи: journalctl -u solarbalance-bot -n 50"
        return 1
    fi
}

# Проверка после обновления
post_update_check() {
    log_info "Проверка после обновления..."
    
    # Проверяем статус сервиса
    if systemctl is-active --quiet solarbalance-bot; then
        log_success "✅ Сервис работает"
    else
        log_error "❌ Сервис не работает"
    fi
    
    # Проверяем логи на ошибки
    local error_count=$(journalctl -u solarbalance-bot --since "5 minutes ago" | grep -i error | wc -l)
    if [[ $error_count -gt 0 ]]; then
        log_warning "⚠️ Найдено $error_count ошибок в логах"
    else
        log_success "✅ Ошибок в логах не найдено"
    fi
    
    # Проверяем процесс
    local process_count=$(pgrep -f "python.*main.py" | wc -l)
    if [[ $process_count -gt 0 ]]; then
        log_success "✅ Процесс бота запущен"
    else
        log_error "❌ Процесс бота не найден"
    fi
}

# Главная функция
main() {
    echo "🔄 Обновление существующей установки Solar Balance Bot"
    echo "=================================================="
    echo ""
    
    check_root
    
    # Поиск существующей установки
    if ! find_existing_installation; then
        exit 1
    fi
    
    # Получаем путь к установке
    local install_path=""
    possible_paths=(
        "/home/solarbot/solarbalance"
        "/home/solarbalance/solarbalance"
        "/home/solarbalance/solarbalance-bot"
        "/opt/solarbalance"
        "/var/www/solarbalance"
    )
    
    for path in "${possible_paths[@]}"; do
        if [[ -d "$path" && -f "$path/main.py" ]]; then
            install_path="$path"
            break
        fi
    done
    
    if [[ -z "$install_path" ]]; then
        read -p "Введите путь к существующей установке: " install_path
        if [[ ! -d "$install_path" || ! -f "$install_path/main.py" ]]; then
            log_error "Неверный путь к установке"
            exit 1
        fi
    fi
    
    log_info "Путь к установке: $install_path"
    
    # Подтверждение обновления
    echo ""
    log_warning "ВНИМАНИЕ: Будет выполнено обновление существующей установки!"
    log_info "Путь: $install_path"
    read -p "Продолжить обновление? (y/N): " confirm
    
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log_info "Обновление отменено"
        exit 0
    fi
    
    # Выполняем обновление
    create_backup "$install_path"
    stop_service
    update_code "$install_path"
    update_dependencies "$install_path"
    update_systemd_service "$install_path"
    check_configuration "$install_path"
    start_service
    post_update_check
    
    echo ""
    log_success "🎉 Обновление завершено успешно!"
    echo ""
    echo "📝 Следующие шаги:"
    echo "1. Проверьте работу бота в Telegram"
    echo "2. Проверьте логи: journalctl -u solarbalance-bot -f"
    echo "3. При необходимости отредактируйте .env файл"
    echo ""
    echo "🔧 Полезные команды:"
    echo "   sudo systemctl status solarbalance-bot"
    echo "   sudo journalctl -u solarbalance-bot -f"
    echo "   check-solarbot (если доступен)"
    echo ""
}

# Запуск главной функции
main "$@" 