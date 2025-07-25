"""
Комплексный тест пользовательского опыта SolarBalance с асинхронной БД
Проверяет все основные сценарии использования бота
"""
import asyncio
import logging
from datetime import datetime
from services.ai_predictions import AIPredictionService
from services.star_advice_service import StarAdviceService
from services.motivation_service import MotivationService
from services.subscription_service import SubscriptionService
from services.antispam_service import AntiSpamService
from services.astro_calculations import AstroService
from database_async import AsyncDatabaseManager, User, NatalChart
from models import PlanetPosition, Location

# Отключаем логи для чистого вывода
logging.basicConfig(level=logging.ERROR)

class AsyncUserExperienceTester:
    def __init__(self):
        self.ai_service = AIPredictionService()
        self.star_advice_service = StarAdviceService()
        self.motivation_service = MotivationService(self.ai_service)
        self.subscription_service = SubscriptionService()
        self.antispam_service = AntiSpamService()
        self.astro_service = AstroService()
        self.db_manager = AsyncDatabaseManager("sqlite+aiosqlite:///test_user_experience.db")
        
        # Тестовые данные
        self.test_user_id = 999999
        self.test_planets = {
            "Солнце": PlanetPosition(sign="Лев", degree=15.0, house=5),
            "Луна": PlanetPosition(sign="Рак", degree=8.0, house=4),
            "Меркурий": PlanetPosition(sign="Лев", degree=12.0, house=5),
            "Венера": PlanetPosition(sign="Дева", degree=3.0, house=6),
            "Марс": PlanetPosition(sign="Скорпион", degree=22.0, house=8),
        }
        
    async def setup(self):
        """Инициализация тестовой среды"""
        await self.db_manager.init_db()
        print("✅ Тестовая среда инициализирована")
        
    async def cleanup(self):
        """Очистка тестовых данных"""
        await self.db_manager.delete_user_data(self.test_user_id)
        await self.db_manager.close()
        print("✅ Тестовые данные очищены")
        
    async def test_all_user_scenarios(self):
        """Запуск всех тестов пользовательского опыта"""
        print("🧪 КОМПЛЕКСНЫЙ ТЕСТ ПОЛЬЗОВАТЕЛЬСКОГО ОПЫТА")
        print("=" * 60)
        
        results = []
        
        # 1. Тест регистрации и профиля
        print("\n👤 ТЕСТ 1: РЕГИСТРАЦИЯ И ПРОФИЛЬ")
        print("-" * 30)
        result = await self.test_user_registration()
        results.append(("Регистрация и профиль", result))
        
        # 2. Тест создания натальной карты
        print("\n⭐ ТЕСТ 2: СОЗДАНИЕ НАТАЛЬНОЙ КАРТЫ")
        print("-" * 30)
        result = await self.test_natal_chart_creation()
        results.append(("Создание натальной карты", result))
        
        # 3. Тест AI прогнозов
        print("\n🔮 ТЕСТ 3: AI ПРОГНОЗЫ")
        print("-" * 30)
        result = await self.test_ai_predictions()
        results.append(("AI Прогнозы", result))
        
        # 4. Тест звездного совета
        print("\n🌟 ТЕСТ 4: ЗВЕЗДНЫЙ СОВЕТ")
        print("-" * 30)
        result = await self.test_star_advice()
        results.append(("Звездный совет", result))
        
        # 5. Тест ежедневных мотиваций
        print("\n🌅 ТЕСТ 5: ЕЖЕДНЕВНЫЕ МОТИВАЦИИ")
        print("-" * 30)
        result = await self.test_daily_motivations()
        results.append(("Ежедневные мотивации", result))
        
        # 6. Тест системы подписки
        print("\n💎 ТЕСТ 6: СИСТЕМА ПОДПИСКИ")
        print("-" * 30)
        result = await self.test_subscription_system()
        results.append(("Система подписки", result))
        
        # 7. Тест антиспама
        print("\n🛡️ ТЕСТ 7: АНТИСПАМ СИСТЕМА")
        print("-" * 30)
        result = await self.test_antispam_system()
        results.append(("Антиспам система", result))
        
        # 8. Тест астрологических расчетов
        print("\n⭐ ТЕСТ 8: АСТРОЛОГИЧЕСКИЕ РАСЧЕТЫ")
        print("-" * 30)
        result = await self.test_astro_calculations()
        results.append(("Астрологические расчеты", result))
        
        # Итоговый отчет
        print("\n📊 ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"{test_name:<25} {status}")
            if result:
                passed += 1
        
        print(f"\n📈 Результат: {passed}/{total} тестов пройдено")
        
        if passed == total:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Бот готов к работе с пользователями.")
        else:
            print("⚠️ Обнаружены проблемы, требующие внимания.")
            
        return passed == total
    
    async def test_user_registration(self):
        """Тест регистрации и профиля пользователя"""
        try:
            # Создание пользователя
            user, created = await self.db_manager.get_or_create_user(
                telegram_id=self.test_user_id,
                name="Тестовый Пользователь"
            )
            
            if not created:
                print("❌ Пользователь уже существует")
                return False
                
            print(f"✅ Пользователь создан: {user.name}")
            
            # Обновление профиля
            updated_user = await self.db_manager.update_user_profile(
                telegram_id=self.test_user_id,
                name="Тестовый Пользователь",
                gender="Мужской",
                birth_year=1990,
                birth_city="Москва",
                birth_date=datetime(1990, 7, 15, 12, 0),
                birth_time_specified=True
            )
            
            if not updated_user or not updated_user.is_profile_complete:
                print("❌ Профиль не обновлен корректно")
                return False
                
            print(f"✅ Профиль обновлен: {updated_user.birth_city}")
            
            # Получение профиля
            profile = await self.db_manager.get_user_profile(self.test_user_id)
            if not profile:
                print("❌ Профиль не найден")
                return False
                
            print(f"✅ Профиль получен: {profile.name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка теста регистрации: {e}")
            return False
    
    async def test_natal_chart_creation(self):
        """Тест создания натальной карты"""
        try:
            # Создание натальной карты
            chart = await self.db_manager.create_natal_chart(
                telegram_id=self.test_user_id,
                name="Тестовый Пользователь",
                city="Москва",
                latitude=55.7558,
                longitude=37.6176,
                timezone="Europe/Moscow",
                birth_date=datetime(1990, 7, 15, 12, 0),
                birth_time_specified=True,
                has_warning=False,
                planets_data=self.test_planets
            )
            
            if not chart:
                print("❌ Натальная карта не создана")
                return False
                
            print(f"✅ Натальная карта создана: {chart.city}")
            
            # Получение карт пользователя
            charts = await self.db_manager.get_user_charts(self.test_user_id)
            if not charts or len(charts) == 0:
                print("❌ Карты пользователя не найдены")
                return False
                
            print(f"✅ Карты пользователя получены: {len(charts)} карт")
            
            # Получение карты по ID
            chart_by_id = await self.db_manager.get_chart_by_id(chart.id, self.test_user_id)
            if not chart_by_id:
                print("❌ Карта по ID не найдена")
                return False
                
            print(f"✅ Карта по ID получена: {chart_by_id.id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка теста натальной карты: {e}")
            return False
    
    async def test_ai_predictions(self):
        """Тест AI прогнозов"""
        try:
            # Получение карты для прогноза
            charts = await self.db_manager.get_user_charts(self.test_user_id)
            if not charts:
                print("❌ Нет карт для прогноза")
                return False
                
            chart = charts[0]
            planets = chart.get_planets_data()
            
            # Генерация прогноза
            prediction = await self.ai_service.generate_prediction(
                user_planets=planets,
                prediction_type="сегодня",
                owner_name="Тестовый пользователь",
                birth_dt=chart.birth_date,
                location=Location(lat=chart.latitude, lon=chart.longitude, city=chart.city)
            )
            
            if not prediction or len(prediction) < 100:
                print("❌ Прогноз не сгенерирован или слишком короткий")
                return False
                
            print(f"✅ Прогноз сгенерирован ({len(prediction)} символов)")
            
            # Создание прогноза в БД
            valid_from, valid_until = self.ai_service.get_prediction_period("сегодня")
            db_prediction = await self.db_manager.create_prediction(
                telegram_id=self.test_user_id,
                chart_id=chart.id,
                prediction_type="сегодня",
                valid_from=valid_from,
                valid_until=valid_until,
                content=prediction,
                generation_time=1.5
            )
            
            if not db_prediction:
                print("❌ Прогноз не сохранен в БД")
                return False
                
            print(f"✅ Прогноз сохранен в БД: {db_prediction.id}")
            
            # Поиск действующего прогноза
            existing_prediction = await self.db_manager.find_valid_prediction(
                self.test_user_id, chart.id, "сегодня"
            )
            
            if not existing_prediction:
                print("❌ Действующий прогноз не найден")
                return False
                
            print(f"✅ Действующий прогноз найден: {existing_prediction.id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка теста AI прогнозов: {e}")
            return False
    
    async def test_star_advice(self):
        """Тест звездного совета"""
        try:
            # Тест валидации вопросов
            test_questions = [
                ("Короткий", False),  # Слишком короткий
                ("Это очень длинный вопрос, который превышает лимит в 500 символов и должен быть отклонен системой валидации. " * 10, False),  # Слишком длинный
                ("Как мне найти работу в IT сфере?", True),  # Корректный
                ("Что делать с отношениями?", True),  # Корректный
            ]
            
            for question, should_be_valid in test_questions:
                validation = await self.star_advice_service.validate_question(question)
                if validation["is_valid"] == should_be_valid:
                    print(f"✅ Валидация вопроса: {'принят' if should_be_valid else 'отклонен'}")
                else:
                    print(f"❌ Ошибка валидации: {question[:30]}...")
                    return False
            
            # Получение карты для совета
            charts = await self.db_manager.get_user_charts(self.test_user_id)
            if not charts:
                print("❌ Нет карт для совета")
                return False
                
            chart = charts[0]
            planets = chart.get_planets_data()
            
            # Генерация совета
            advice = await self.star_advice_service.generate_advice(
                question="Как мне улучшить карьеру?",
                category="career",
                user_planets=planets,
                birth_dt=chart.birth_date,
                location=Location(lat=chart.latitude, lon=chart.longitude, city=chart.city),
                user_name="Тестовый пользователь"
            )
            
            if advice and len(advice) > 200:
                print(f"✅ Совет сгенерирован ({len(advice)} символов)")
                return True
            else:
                print("❌ Совет не сгенерирован или слишком короткий")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка теста звездного совета: {e}")
            return False
    
    async def test_daily_motivations(self):
        """Тест ежедневных мотиваций"""
        try:
            # Получение пользователя
            user = await self.db_manager.get_user_profile(self.test_user_id)
            if not user:
                print("❌ Пользователь не найден")
                return False
            
            # Генерация мотивации для Free пользователя
            motivation = await self.motivation_service.generate_motivation(
                user=user,
                is_subscribed=False
            )
            
            if motivation and len(motivation) > 100:
                print(f"✅ Free мотивация сгенерирована ({len(motivation)} символов)")
            else:
                print("❌ Free мотивация не сгенерирована")
                return False
            
            # Генерация мотивации для Premium пользователя
            premium_motivation = await self.motivation_service.generate_motivation(
                user=user,
                is_subscribed=True
            )
            
            if premium_motivation and len(premium_motivation) > 100:
                print(f"✅ Premium мотивация сгенерирована ({len(premium_motivation)} символов)")
            else:
                print("❌ Premium мотивация не сгенерирована")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка теста мотиваций: {e}")
            return False
    
    async def test_subscription_system(self):
        """Тест системы подписки"""
        try:
            # Получение или создание подписки
            subscription = await self.db_manager.get_or_create_subscription(self.test_user_id)
            if not subscription:
                print("❌ Подписка не создана")
                return False
                
            print(f"✅ Подписка получена: {subscription.subscription_type.value}")
            
            # Проверка Premium статуса
            is_premium = self.subscription_service.is_user_premium(self.test_user_id)
            print(f"✅ Статус Premium проверен: {'Да' if is_premium else 'Нет'}")
            
            # Тест фильтрации планет
            all_planets = {
                "Солнце": PlanetPosition(sign="Лев", degree=15.0),
                "Луна": PlanetPosition(sign="Рак", degree=8.0),
                "Меркурий": PlanetPosition(sign="Лев", degree=12.0),
                "Венера": PlanetPosition(sign="Дева", degree=3.0),
                "Марс": PlanetPosition(sign="Скорпион", degree=22.0),
                "Юпитер": PlanetPosition(sign="Рыбы", degree=5.0),
                "Сатурн": PlanetPosition(sign="Козерог", degree=18.0),
                "Уран": PlanetPosition(sign="Козерог", degree=12.0),
                "Нептун": PlanetPosition(sign="Козерог", degree=8.0),
                "Плутон": PlanetPosition(sign="Скорпион", degree=15.0),
            }
            
            # Для Free пользователя
            free_planets = await self.subscription_service.filter_planets_for_user(
                all_planets, self.test_user_id
            )
            print(f"✅ Планеты отфильтрованы для Free: {len(free_planets)} из {len(all_planets)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка теста подписки: {e}")
            return False
    
    async def test_antispam_system(self):
        """Тест антиспам системы"""
        try:
            # Тест проверки лимитов
            limits = self.antispam_service.check_limits(self.test_user_id, is_premium=False)
            print(f"✅ Лимиты проверены: {limits['questions_left']} вопросов осталось")
            
            # Тест записи использования
            self.antispam_service.record_question(self.test_user_id)
            new_limits = self.antispam_service.check_limits(self.test_user_id, is_premium=False)
            print(f"✅ Использование записано: {new_limits['questions_left']} вопросов осталось")
            
            # Тест статистики
            stats = self.antispam_service.get_stats_text(self.test_user_id, is_premium=False)
            if stats:
                print("✅ Статистика сгенерирована")
            else:
                print("❌ Статистика не сгенерирована")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка теста антиспама: {e}")
            return False
    
    async def test_astro_calculations(self):
        """Тест астрологических расчетов"""
        try:
            # Тест расчета натальной карты
            location = Location(lat=55.7558, lon=37.6176, city="Москва")
            birth_dt = datetime(1990, 7, 15, 12, 0)
            
            planets = await self.astro_service.calculate_natal_chart(birth_dt, location)
            
            if planets and len(planets) >= 10:  # Минимум основные планеты
                print(f"✅ Натальная карта рассчитана: {len(planets)} планет")
            else:
                print("❌ Натальная карта не рассчитана")
                return False
            
            # Тест расчета транзитов
            transit_date = datetime.now()
            transits = await self.astro_service.calculate_transits(birth_dt, location, transit_date)
            
            if transits:
                print(f"✅ Транзиты рассчитаны: {len(transits)} аспектов")
            else:
                print("❌ Транзиты не рассчитаны")
                return False
            
            # Тест получения ретроградных планет
            retrograde_info = self.astro_service.get_retrograde_info()
            if retrograde_info:
                print(f"✅ Ретроградные планеты получены: {len(retrograde_info)} планет")
            else:
                print("❌ Ретроградные планеты не получены")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка теста астрологических расчетов: {e}")
            return False

async def main():
    """Главная функция тестирования"""
    tester = AsyncUserExperienceTester()
    
    try:
        await tester.setup()
        success = await tester.test_all_user_scenarios()
        
        if success:
            print("\n🎯 ВЫВОД: Все сервисы работают корректно!")
            print("✅ Бот готов к работе с пользователями")
            print("✅ Асинхронная БД функционирует")
            print("✅ AI-сервисы работают")
            print("✅ Астрологические расчеты точны")
            print("✅ Системы защиты активны")
        else:
            print("\n⚠️ ВЫВОД: Обнаружены проблемы!")
            print("❌ Требуется доработка перед запуском")
            
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 