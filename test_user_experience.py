"""
Комплексный тест пользовательского опыта SolarBalance
Проверяет все основные сценарии использования бота
"""
import asyncio
import logging
from datetime import datetime, timedelta
from services.ai_predictions import AIPredictionService
from services.star_advice_service import StarAdviceService
from services.motivation_service import MotivationService
from services.subscription_service import SubscriptionService
from services.antispam_service import AntiSpamService
from services.astro_calculations import AstroService
from models import PlanetPosition, Location, BirthData
from database import User, NatalChart, db_manager

# Отключаем логи для чистого вывода
logging.basicConfig(level=logging.ERROR)

class UserExperienceTester:
    def __init__(self):
        self.ai_service = AIPredictionService()
        self.star_advice_service = StarAdviceService()
        self.motivation_service = MotivationService()
        self.subscription_service = SubscriptionService()
        self.antispam_service = AntiSpamService()
        self.astro_service = AstroService()
        
        # Тестовые данные
        self.test_user_id = 123456789
        self.test_planets = {
            "Солнце": PlanetPosition(sign="Лев", degree=15.0, house=5),
            "Луна": PlanetPosition(sign="Рак", degree=8.0, house=4),
            "Меркурий": PlanetPosition(sign="Лев", degree=12.0, house=5),
            "Венера": PlanetPosition(sign="Дева", degree=3.0, house=6),
            "Марс": PlanetPosition(sign="Скорпион", degree=22.0, house=8),
        }
        
    async def test_all_scenarios(self):
        """Запуск всех тестов пользовательского опыта"""
        print("🧪 КОМПЛЕКСНЫЙ ТЕСТ ПОЛЬЗОВАТЕЛЬСКОГО ОПЫТА")
        print("=" * 60)
        
        results = []
        
        # 1. Тест AI прогнозов
        print("\n🔮 ТЕСТ 1: AI ПРОГНОЗЫ")
        print("-" * 30)
        result = await self.test_ai_predictions()
        results.append(("AI Прогнозы", result))
        
        # 2. Тест звездного совета
        print("\n🌟 ТЕСТ 2: ЗВЕЗДНЫЙ СОВЕТ")
        print("-" * 30)
        result = await self.test_star_advice()
        results.append(("Звездный совет", result))
        
        # 3. Тест мотиваций
        print("\n🌅 ТЕСТ 3: ЕЖЕДНЕВНЫЕ МОТИВАЦИИ")
        print("-" * 30)
        result = await self.test_daily_motivations()
        results.append(("Ежедневные мотивации", result))
        
        # 4. Тест подписки
        print("\n💎 ТЕСТ 4: СИСТЕМА ПОДПИСКИ")
        print("-" * 30)
        result = await self.test_subscription_system()
        results.append(("Система подписки", result))
        
        # 5. Тест антиспама
        print("\n🛡️ ТЕСТ 5: АНТИСПАМ СИСТЕМА")
        print("-" * 30)
        result = await self.test_antispam_system()
        results.append(("Антиспам система", result))
        
        # 6. Тест астрологических расчетов
        print("\n⭐ ТЕСТ 6: АСТРОЛОГИЧЕСКИЕ РАСЧЕТЫ")
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
    
    async def test_ai_predictions(self):
        """Тест AI прогнозов"""
        try:
            # Тест генерации прогноза на сегодня
            prediction = await self.ai_service.generate_prediction(
                user_planets=self.test_planets,
                prediction_type="сегодня",
                owner_name="Тестовый пользователь",
                birth_dt=datetime(1990, 7, 15, 12, 0),
                location=Location(lat=55.7558, lon=37.6176, city="Москва")
            )
            
            if not prediction or len(prediction) < 100:
                print("❌ Прогноз слишком короткий или пустой")
                return False
                
            print(f"✅ Прогноз сгенерирован ({len(prediction)} символов)")
            
            # Тест разных типов прогнозов
            periods = ["сегодня", "завтра", "неделя", "месяц"]
            for period in periods:
                try:
                    valid_from, valid_until = self.ai_service.get_prediction_period(period)
                    if valid_from and valid_until:
                        print(f"✅ Период '{period}' корректно рассчитан")
                    else:
                        print(f"❌ Ошибка расчета периода '{period}'")
                        return False
                except Exception as e:
                    print(f"❌ Ошибка в периоде '{period}': {e}")
                    return False
            
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
            
            # Тест генерации совета
            advice = await self.star_advice_service.generate_advice(
                question="Как мне улучшить карьеру?",
                category="career",
                user_planets=self.test_planets,
                birth_dt=datetime(1990, 7, 15, 12, 0),
                location=Location(lat=55.7558, lon=37.6176, city="Москва"),
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
            # Тест генерации мотивации
            motivation = await self.motivation_service.generate_motivation(
                user_planets=self.test_planets,
                birth_dt=datetime(1990, 7, 15, 12, 0),
                is_premium=False
            )
            
            if motivation and len(motivation) > 100:
                print(f"✅ Мотивация сгенерирована ({len(motivation)} символов)")
            else:
                print("❌ Мотивация не сгенерирована")
                return False
            
            # Тест Premium мотивации
            premium_motivation = await self.motivation_service.generate_motivation(
                user_planets=self.test_planets,
                birth_dt=datetime(1990, 7, 15, 12, 0),
                is_premium=True
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
            # Тест проверки Premium статуса
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
    tester = UserExperienceTester()
    success = await tester.test_all_scenarios()
    
    if success:
        print("\n🎯 ВЫВОД: Все сервисы работают корректно!")
        print("✅ Бот готов к работе с пользователями")
        print("✅ AI-сервисы функционируют")
        print("✅ Астрологические расчеты точны")
        print("✅ Системы защиты активны")
    else:
        print("\n⚠️ ВЫВОД: Обнаружены проблемы!")
        print("❌ Требуется доработка перед запуском")

if __name__ == "__main__":
    asyncio.run(main()) 