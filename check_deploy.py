#!/usr/bin/env python3
"""
Скрипт проверки готовности SolarBalance к деплою
Проверяет все критические компоненты перед развертыванием
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import List, Tuple, Dict, Any
import traceback

# Цвета для консоли
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message: str, status: str = "INFO"):
    """Печать статуса с цветами"""
    color = Colors.GREEN if status == "OK" else Colors.RED if status == "ERROR" else Colors.YELLOW
    print(f"{color}[{status}]{Colors.END} {message}")

def print_header(message: str):
    """Печать заголовка"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== {message} ==={Colors.END}")

class DeployChecker:
    """Класс для проверки готовности к деплою"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_total = 0
    
    def add_error(self, message: str):
        """Добавить ошибку"""
        self.errors.append(message)
        print_status(message, "ERROR")
    
    def add_warning(self, message: str):
        """Добавить предупреждение"""
        self.warnings.append(message)
        print_status(message, "WARN")
    
    def add_success(self, message: str):
        """Добавить успешную проверку"""
        self.checks_passed += 1
        print_status(message, "OK")
    
    def check_python_version(self) -> bool:
        """Проверка версии Python"""
        print_header("Проверка Python")
        self.checks_total += 1
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 9:
            self.add_success(f"Python {version.major}.{version.minor}.{version.micro} - OK")
            return True
        else:
            self.add_error(f"Python {version.major}.{version.minor}.{version.micro} - требуется 3.9+")
            return False
    
    def check_required_files(self) -> bool:
        """Проверка обязательных файлов"""
        print_header("Проверка файлов")
        
        required_files = [
            "main.py",
            "config.py", 
            "database.py",
            "models.py",
            "utils.py",
            "requirements-prod.txt",
            "env.example",
            "deploy.sh",
            "start_server.sh",
            "DEPLOY_GUIDE.md"
        ]
        
        all_good = True
        for file in required_files:
            self.checks_total += 1
            if Path(file).exists():
                self.add_success(f"Файл {file} найден")
            else:
                self.add_error(f"Файл {file} отсутствует")
                all_good = False
        
        return all_good
    
    def check_directories(self) -> bool:
        """Проверка директорий"""
        print_header("Проверка директорий")
        
        required_dirs = [
            "handlers",
            "services", 
            "tests",
            "handlers/admin",
            "handlers/common",
            "handlers/profile",
            "handlers/natal_chart",
            "handlers/predictions",
            "handlers/compatibility",
            "handlers/star_advice",
            "handlers/sky_map",
            "handlers/subscription"
        ]
        
        all_good = True
        for dir_path in required_dirs:
            self.checks_total += 1
            if Path(dir_path).exists():
                self.add_success(f"Директория {dir_path} найдена")
            else:
                self.add_error(f"Директория {dir_path} отсутствует")
                all_good = False
        
        return all_good
    
    def check_imports(self) -> bool:
        """Проверка импортов"""
        print_header("Проверка импортов")
        
        critical_modules = [
            "aiogram",
            "sqlalchemy", 
            "swisseph",
            "geopy",
            "matplotlib",
            "numpy",
            "scipy",
            "pillow",
            "dotenv",
            "aiohttp",
            "aiosqlite",
            "apscheduler",
            "skyfield",
            "openai",
            "timezonefinder"
        ]
        
        all_good = True
        for module in critical_modules:
            self.checks_total += 1
            try:
                if module == "pillow":
                    import PIL
                elif module == "dotenv":
                    import dotenv
                else:
                    __import__(module)
                self.add_success(f"Модуль {module} доступен")
            except ImportError:
                self.add_error(f"Модуль {module} не найден")
                all_good = False
        
        return all_good
    
    def check_config(self) -> bool:
        """Проверка конфигурации"""
        print_header("Проверка конфигурации")
        
        try:
            # Проверяем импорт config
            self.checks_total += 1
            from config import Config
            self.add_success("Модуль config импортирован")
            
            # Проверяем .env файл
            self.checks_total += 1
            if Path(".env").exists():
                self.add_success("Файл .env найден")
                
                # Проверяем критические переменные
                from dotenv import load_dotenv
                load_dotenv()
                
                critical_vars = ["BOT_TOKEN", "ADMIN_IDS"]
                for var in critical_vars:
                    self.checks_total += 1
                    if os.getenv(var):
                        self.add_success(f"Переменная {var} установлена")
                    else:
                        self.add_error(f"Переменная {var} не найдена в .env")
                
                # Проверяем опциональные переменные
                optional_vars = ["AI_API", "YANDEX_API_KEY", "DATABASE_URL"]
                for var in optional_vars:
                    self.checks_total += 1
                    if os.getenv(var):
                        self.add_success(f"Переменная {var} установлена")
                    else:
                        self.add_warning(f"Переменная {var} не установлена (опционально)")
                
            else:
                self.add_error("Файл .env не найден")
                return False
                
            return True
            
        except Exception as e:
            self.add_error(f"Ошибка проверки конфигурации: {e}")
            return False
    
    def check_database(self) -> bool:
        """Проверка базы данных"""
        print_header("Проверка базы данных")
        
        try:
            self.checks_total += 1
            from database import DatabaseManager
            self.add_success("Модуль database импортирован")
            
            # Пробуем создать менеджер БД
            self.checks_total += 1
            try:
                db_manager = DatabaseManager("sqlite:///test_deploy.db")
                self.add_success("DatabaseManager создан")
                
                # Удаляем тестовую БД
                test_db = Path("test_deploy.db")
                if test_db.exists():
                    test_db.unlink()
                    
            except Exception as e:
                self.add_error(f"Ошибка создания DatabaseManager: {e}")
                return False
                
            return True
            
        except Exception as e:
            self.add_error(f"Ошибка импорта database: {e}")
            return False
    
    def check_services(self) -> bool:
        """Проверка сервисов"""
        print_header("Проверка сервисов")
        
        services = [
            "services.astro_calculations",
            "services.subscription_service",
            "services.ai_predictions",
            "services.geocoding_service",
            "services.sky_visualization_service"
        ]
        
        all_good = True
        for service in services:
            self.checks_total += 1
            try:
                __import__(service)
                self.add_success(f"Сервис {service} доступен")
            except ImportError as e:
                self.add_error(f"Сервис {service} не найден: {e}")
                all_good = False
        
        return all_good
    
    def check_handlers(self) -> bool:
        """Проверка обработчиков"""
        print_header("Проверка обработчиков")
        
        handlers = [
            "handlers.admin.router",
            "handlers.common.router",
            "handlers.profile.router",
            "handlers.natal_chart.router",
            "handlers.predictions.router",
            "handlers.compatibility.router",
            "handlers.star_advice.router",
            "handlers.sky_map.router",
            "handlers.subscription.router"
        ]
        
        all_good = True
        for handler in handlers:
            self.checks_total += 1
            try:
                __import__(handler)
                self.add_success(f"Обработчик {handler} доступен")
            except ImportError as e:
                self.add_error(f"Обработчик {handler} не найден: {e}")
                all_good = False
        
        return all_good
    
    def check_ephemeris_files(self) -> bool:
        """Проверка файлов эфемерид"""
        print_header("Проверка файлов эфемерид")
        
        ephemeris_files = [
            "de421.bsp",
            "de422.bsp"
        ]
        
        found_files = []
        for file in ephemeris_files:
            self.checks_total += 1
            if Path(file).exists():
                self.add_success(f"Файл эфемерид {file} найден")
                found_files.append(file)
            else:
                self.add_warning(f"Файл эфемерид {file} не найден")
        
        if not found_files:
            self.add_warning("Файлы эфемерид не найдены. Скачайте их перед деплоем.")
        
        return len(found_files) > 0
    
    def check_permissions(self) -> bool:
        """Проверка прав доступа"""
        print_header("Проверка прав доступа")
        
        executable_files = [
            "deploy.sh",
            "start_server.sh"
        ]
        
        all_good = True
        for file in executable_files:
            self.checks_total += 1
            file_path = Path(file)
            if file_path.exists():
                if os.access(file_path, os.X_OK):
                    self.add_success(f"Файл {file} исполняемый")
                else:
                    self.add_warning(f"Файл {file} не исполняемый (chmod +x {file})")
            else:
                self.add_error(f"Файл {file} не найден")
                all_good = False
        
        return all_good
    
    def check_security(self) -> bool:
        """Проверка безопасности"""
        print_header("Проверка безопасности")
        
        security_checks = []
        
        # Проверка .env файла
        self.checks_total += 1
        env_file = Path(".env")
        if env_file.exists():
            stat = env_file.stat()
            if stat.st_mode & 0o077:  # Проверяем права доступа
                self.add_warning("Файл .env доступен для чтения другими пользователями")
            else:
                self.add_success("Права доступа к .env файлу корректны")
        
        # Проверка наличия секретных ключей в коде
        self.checks_total += 1
        try:
            with open("config.py", "r", encoding="utf-8") as f:
                content = f.read()
                if "your-secret-key-change-me" in content:
                    self.add_warning("Используется дефолтный SECRET_KEY")
                else:
                    self.add_success("SECRET_KEY изменен")
        except:
            self.add_warning("Не удалось проверить SECRET_KEY")
        
        return True
    
    def run_all_checks(self) -> bool:
        """Запуск всех проверок"""
        print(f"{Colors.BOLD}{Colors.BLUE}🔍 Проверка готовности SolarBalance к деплою{Colors.END}\n")
        
        checks = [
            self.check_python_version,
            self.check_required_files,
            self.check_directories,
            self.check_imports,
            self.check_config,
            self.check_database,
            self.check_services,
            self.check_handlers,
            self.check_ephemeris_files,
            self.check_permissions,
            self.check_security
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.add_error(f"Ошибка при выполнении проверки {check.__name__}: {e}")
                print(f"Полная ошибка: {traceback.format_exc()}")
        
        return self.print_summary()
    
    def print_summary(self) -> bool:
        """Печать итогового отчета"""
        print_header("Итоговый отчет")
        
        print(f"✅ Проверок пройдено: {self.checks_passed}/{self.checks_total}")
        
        if self.errors:
            print(f"\n{Colors.RED}❌ КРИТИЧЕСКИЕ ОШИБКИ ({len(self.errors)}):{Colors.END}")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}⚠️  ПРЕДУПРЕЖДЕНИЯ ({len(self.warnings)}):{Colors.END}")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        success_rate = (self.checks_passed / self.checks_total) * 100 if self.checks_total > 0 else 0
        
        print(f"\n{Colors.BOLD}Готовность к деплою: {success_rate:.1f}%{Colors.END}")
        
        if not self.errors:
            print(f"\n{Colors.GREEN}🎉 Готов к деплою! Запустите: ./deploy.sh{Colors.END}")
            return True
        else:
            print(f"\n{Colors.RED}❌ Не готов к деплою. Исправьте ошибки выше.{Colors.END}")
            return False

def main():
    """Основная функция"""
    checker = DeployChecker()
    
    try:
        success = checker.run_all_checks()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Проверка прервана пользователем{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Критическая ошибка: {e}{Colors.END}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 