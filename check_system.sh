#!/bin/bash

# 🔍 Проверка системы перед установкой SolarBalance
# Использование: ./check_system.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Счетчики
PASSED=0
FAILED=0
WARNINGS=0

# Функции для вывода
print_header() {
    echo -e "${BLUE}"
    echo "🔍 Проверка готовности системы к установке SolarBalance"
    echo "======================================================="
    echo -e "${NC}"
}

print_check() {
    echo -e "${BLUE}[ПРОВЕРКА]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[✓ ПРОЙДЕНО]${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}[✗ ОШИБКА]${NC} $1"
    ((FAILED++))
}

print_warning() {
    echo -e "${YELLOW}[⚠ ПРЕДУПРЕЖДЕНИЕ]${NC} $1"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Проверка прав root
check_root() {
    print_check "Проверка прав суперпользователя..."
    if [[ $EUID -eq 0 ]]; then
        print_pass "Скрипт запущен с правами root"
    else
        print_warning "Скрипт запущен не от root. Некоторые проверки могут быть недоступны"
    fi
}

# Проверка операционной системы
check_os() {
    print_check "Проверка операционной системы..."
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        print_info "ОС: $PRETTY_NAME"
        
        case $ID in
            ubuntu)
                if [[ $(echo "$VERSION_ID >= 20.04" | bc -l) -eq 1 ]]; then
                    print_pass "Ubuntu 20.04+ поддерживается"
                else
                    print_warning "Рекомендуется Ubuntu 20.04 или новее (текущая: $VERSION_ID)"
                fi
                ;;
            debian)
                if [[ $(echo "$VERSION_ID >= 11" | bc -l) -eq 1 ]]; then
                    print_pass "Debian 11+ поддерживается"
                else
                    print_warning "Рекомендуется Debian 11 или новее (текущая: $VERSION_ID)"
                fi
                ;;
            centos|rhel)
                if [[ $(echo "$VERSION_ID >= 8" | bc -l) -eq 1 ]]; then
                    print_pass "CentOS/RHEL 8+ поддерживается"
                else
                    print_warning "Рекомендуется CentOS/RHEL 8 или новее (текущая: $VERSION_ID)"
                fi
                ;;
            *)
                print_warning "Нетестированная ОС: $ID. Установка может потребовать доработки"
                ;;
        esac
    else
        print_fail "Не удалось определить операционную систему"
    fi
}

# Проверка архитектуры процессора
check_architecture() {
    print_check "Проверка архитектуры процессора..."
    
    ARCH=$(uname -m)
    case $ARCH in
        x86_64|amd64)
            print_pass "64-битная архитектура поддерживается ($ARCH)"
            ;;
        aarch64|arm64)
            print_pass "ARM64 архитектура поддерживается ($ARCH)"
            ;;
        *)
            print_warning "Нетестированная архитектура: $ARCH"
            ;;
    esac
}

# Проверка ресурсов системы
check_resources() {
    print_check "Проверка системных ресурсов..."
    
    # Проверка RAM
    TOTAL_RAM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [[ $TOTAL_RAM -ge 2048 ]]; then
        print_pass "RAM: ${TOTAL_RAM}MB (достаточно)"
    elif [[ $TOTAL_RAM -ge 1024 ]]; then
        print_warning "RAM: ${TOTAL_RAM}MB (минимум, рекомендуется 2GB+)"
    else
        print_fail "RAM: ${TOTAL_RAM}MB (недостаточно, минимум 1GB)"
    fi
    
    # Проверка дискового пространства
    AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
    AVAILABLE_SPACE_GB=$((AVAILABLE_SPACE / 1024 / 1024))
    if [[ $AVAILABLE_SPACE_GB -ge 10 ]]; then
        print_pass "Свободное место: ${AVAILABLE_SPACE_GB}GB (достаточно)"
    elif [[ $AVAILABLE_SPACE_GB -ge 5 ]]; then
        print_warning "Свободное место: ${AVAILABLE_SPACE_GB}GB (минимум, рекомендуется 10GB+)"
    else
        print_fail "Свободное место: ${AVAILABLE_SPACE_GB}GB (недостаточно, минимум 5GB)"
    fi
    
    # Проверка CPU
    CPU_CORES=$(nproc)
    if [[ $CPU_CORES -ge 2 ]]; then
        print_pass "CPU ядер: $CPU_CORES (оптимально)"
    elif [[ $CPU_CORES -eq 1 ]]; then
        print_warning "CPU ядер: $CPU_CORES (минимум, рекомендуется 2+)"
    else
        print_fail "Не удалось определить количество CPU ядер"
    fi
}

# Проверка Python
check_python() {
    print_check "Проверка Python..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 9 ]]; then
            print_pass "Python $PYTHON_VERSION установлен (совместим)"
        elif [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 8 ]]; then
            print_warning "Python $PYTHON_VERSION может работать, но рекомендуется 3.9+"
        else
            print_fail "Python $PYTHON_VERSION слишком старый, требуется 3.9+"
        fi
    else
        print_fail "Python3 не установлен"
    fi
    
    # Проверка pip
    if command -v pip3 &> /dev/null; then
        print_pass "pip3 установлен"
    else
        print_fail "pip3 не установлен"
    fi
    
    # Проверка venv
    if python3 -m venv --help &> /dev/null; then
        print_pass "python3-venv доступен"
    else
        print_fail "python3-venv не установлен"
    fi
}

# Проверка Git
check_git() {
    print_check "Проверка Git..."
    
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version | awk '{print $3}')
        print_pass "Git $GIT_VERSION установлен"
    else
        print_fail "Git не установлен"
    fi
}

# Проверка сетевых подключений
check_network() {
    print_check "Проверка сетевых подключений..."
    
    # Проверка общего интернет-соединения
    if ping -c 1 8.8.8.8 &> /dev/null; then
        print_pass "Интернет-соединение доступно"
    else
        print_fail "Нет интернет-соединения"
        return
    fi
    
    # Проверка доступа к GitHub
    if curl -s --connect-timeout 5 https://github.com &> /dev/null; then
        print_pass "GitHub доступен"
    else
        print_warning "GitHub недоступен (может потребоваться прокси)"
    fi
    
    # Проверка доступа к Telegram API
    if curl -s --connect-timeout 5 https://api.telegram.org &> /dev/null; then
        print_pass "Telegram API доступен"
    else
        print_warning "Telegram API недоступен (проверьте файрвол)"
    fi
    
    # Проверка доступа к OpenAI
    if curl -s --connect-timeout 5 https://api.openai.com &> /dev/null; then
        print_pass "OpenAI API доступен"
    else
        print_warning "OpenAI API недоступен (проверьте файрвол)"
    fi
}

# Проверка systemd
check_systemd() {
    print_check "Проверка systemd..."
    
    if command -v systemctl &> /dev/null; then
        if systemctl --version &> /dev/null; then
            print_pass "systemd доступен"
        else
            print_fail "systemd не работает корректно"
        fi
    else
        print_fail "systemctl не найден (systemd не установлен)"
    fi
}

# Проверка компиляторов для Python пакетов
check_build_tools() {
    print_check "Проверка инструментов сборки..."
    
    if command -v gcc &> /dev/null; then
        print_pass "GCC компилятор установлен"
    else
        print_fail "GCC компилятор не установлен (нужен для Swiss Ephemeris)"
    fi
    
    if command -v make &> /dev/null; then
        print_pass "Make утилита установлена"
    else
        print_fail "Make утилита не установлена"
    fi
}

# Проверка портов
check_ports() {
    print_check "Проверка используемых портов..."
    
    # Проверяем, что стандартные порты не заняты
    if command -v netstat &> /dev/null; then
        # Проверяем порт 8080 (если планируется webhook)
        if netstat -tuln | grep :8080 &> /dev/null; then
            print_warning "Порт 8080 занят (может понадобиться для webhook)"
        else
            print_pass "Порт 8080 свободен"
        fi
    else
        print_warning "netstat недоступен, проверка портов пропущена"
    fi
}

# Проверка файрвола
check_firewall() {
    print_check "Проверка файрвола..."
    
    if command -v ufw &> /dev/null; then
        UFW_STATUS=$(ufw status | head -1)
        if [[ $UFW_STATUS == *"inactive"* ]]; then
            print_warning "UFW отключен (рекомендуется включить)"
        else
            print_pass "UFW активен"
        fi
    elif command -v firewalld &> /dev/null; then
        if systemctl is-active firewalld &> /dev/null; then
            print_pass "firewalld активен"
        else
            print_warning "firewalld установлен, но не активен"
        fi
    else
        print_warning "Файрвол не обнаружен (рекомендуется установить ufw)"
    fi
}

# Проверка свободных инодов
check_inodes() {
    print_check "Проверка инодов файловой системы..."
    
    INODES_USAGE=$(df -i / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $INODES_USAGE -lt 80 ]]; then
        print_pass "Использование инодов: ${INODES_USAGE}% (в норме)"
    elif [[ $INODES_USAGE -lt 90 ]]; then
        print_warning "Использование инодов: ${INODES_USAGE}% (высокое)"
    else
        print_fail "Использование инодов: ${INODES_USAGE}% (критическое)"
    fi
}

# Финальный отчет
print_summary() {
    echo ""
    echo -e "${BLUE}=======================================================${NC}"
    echo -e "${BLUE}                    ИТОГОВЫЙ ОТЧЕТ${NC}"
    echo -e "${BLUE}=======================================================${NC}"
    
    if [[ $FAILED -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}🎉 ОТЛИЧНО! Система полностью готова к установке${NC}"
        echo -e "${GREEN}✅ Все проверки пройдены: $PASSED${NC}"
        echo ""
        echo -e "${GREEN}Можете приступать к установке:${NC}"
        echo "   wget https://raw.githubusercontent.com/YOUR_USERNAME/solarbalance/main/install_server.sh"
        echo "   chmod +x install_server.sh"
        echo "   sudo ./install_server.sh"
        
    elif [[ $FAILED -eq 0 ]]; then
        echo -e "${YELLOW}⚠️ ХОРОШО! Система готова с предупреждениями${NC}"
        echo -e "${GREEN}✅ Проверки пройдены: $PASSED${NC}"
        echo -e "${YELLOW}⚠️ Предупреждения: $WARNINGS${NC}"
        echo ""
        echo -e "${YELLOW}Установка возможна, но рекомендуется устранить предупреждения${NC}"
        
    else
        echo -e "${RED}❌ ПРОБЛЕМЫ! Система требует доработки${NC}"
        echo -e "${GREEN}✅ Проверки пройдены: $PASSED${NC}"
        echo -e "${YELLOW}⚠️ Предупреждения: $WARNINGS${NC}"
        echo -e "${RED}❌ Ошибки: $FAILED${NC}"
        echo ""
        echo -e "${RED}Устраните критические ошибки перед установкой${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Рекомендации:${NC}"
    if [[ $FAILED -gt 0 ]]; then
        echo "1. Устраните все критические ошибки"
        echo "2. Повторите проверку: ./check_system.sh"
        echo "3. Приступайте к установке"
    else
        echo "1. Подготовьте данные для конфигурации:"
        echo "   - Токен бота от @BotFather"
        echo "   - API ключ Bothub или OpenAI"
        echo "   - Ваш Telegram ID от @userinfobot"
        echo "2. Запустите автоустановку"
    fi
}

# Главная функция
main() {
    print_header
    
    check_root
    check_os
    check_architecture
    check_resources
    check_python
    check_git
    check_build_tools
    check_systemd
    check_network
    check_ports
    check_firewall
    check_inodes
    
    print_summary
}

# Запуск
main "$@" 