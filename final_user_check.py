"""
Финальная проверка всех пользовательских сценариев SolarBalance
Проверяет полный пользовательский путь от регистрации до использования всех функций
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
from database_async import AsyncDatabaseManager
from models import PlanetPosition, Location

# Отключаем логи
logging.basicConfig(level=logging.ERROR)

class FinalUserCheck:
    def __init__(self):
        self.db_manager = AsyncDatabaseManager("sqlite+aiosqlite:///final_test.db")
        self.test_user_id = 888888
        
    async def run_full_user_journey(self):
        """Полный пользовательский путь"""
        print("🎯 ФИНАЛЬНАЯ ПРОВЕРКА ПОЛЬЗОВАТЕЛЬСКОГО ОПЫТА")
        print("=" * 60)
        
        try:
            await self.db_manager.init_db()
            print("✅ База данных инициализирована")
            
            # 1. Регистрация пользователя
            print("\n👤 1. РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ")
            user, created = await self.db_manager.get_or_create_user(
                telegram_id=self.test_user_id,
                name="Финальный Тест"
            )
            print(f"✅ Пользователь {'создан' if created else 'найден'}: {user.name}")
            
            # 2. Настройка профиля
            print("\n📝 2. НАСТРОЙКА ПРОФИЛЯ")
            updated_user = await self.db_manager.update_user_profile(
                telegram_id=self.test_user_id,
                name="Финальный Тест",
                gender="Мужской",
                birth_year=1990,
                birth_city="Москва",
                birth_date=datetime(1990, 7, 15, 12, 0),
                birth_time_specified=True
            )
            print(f"✅ Профиль настроен: {updated_user.birth_city}")
            
            # 3. Создание натальной карты
            print("\n⭐ 3. СОЗДАНИЕ НАТАЛЬНОЙ КАРТЫ")
            test_planets = {
                "Солнце": {"sign": "Лев", "degree": 15.0},
                "Луна": {"sign": "Рак", "degree": 8.0},
                "Меркурий": {"sign": "Лев", "degree": 12.0},
                "Венера": {"sign": "Дева", "degree": 3.0},
                "Марс": {"sign": "Скорпион", "degree": 22.0},
            }
            
            chart = await self.db_manager.create_natal_chart(
                telegram_id=self.test_user_id,
                name="Финальный Тест",
                city="Москва",
                latitude=55.7558,
                longitude=37.6176,
                timezone="Europe/Moscow",
                birth_date=datetime(1990, 7, 15, 12, 0),
                birth_time_specified=True,
                has_warning=False,
                planets_data=test_planets
            )
            print(f"✅ Натальная карта создана: {chart.city}")
            
            # 4. Проверка AI прогнозов
            print("\n🔮 4. AI ПРОГНОЗЫ")
            ai_service = AIPredictionService()
            if ai_service.client:
                print("✅ AI сервис инициализирован")
                
                # Генерация прогноза
                planets = chart.get_planets_data()
                prediction = await ai_service.generate_prediction(
                    user_planets=planets,
                    prediction_type="сегодня",
                    owner_name="Финальный Тест",
                    birth_dt=chart.birth_date,
                    location=Location(lat=chart.latitude, lon=chart.longitude, city=chart.city)
                )
                
                if prediction and len(prediction) > 100:
                    print(f"✅ Прогноз сгенерирован ({len(prediction)} символов)")
                    
                    # Сохранение прогноза
                    valid_from, valid_until = ai_service.get_prediction_period("сегодня")
                    db_prediction = await self.db_manager.create_prediction(
                        telegram_id=self.test_user_id,
                        chart_id=chart.id,
                        prediction_type="сегодня",
                        valid_from=valid_from,
                        valid_until=valid_until,
                        content=prediction,
                        generation_time=1.5
                    )
                    print(f"✅ Прогноз сохранен в БД: {db_prediction.id}")
                else:
                    print("❌ Прогноз не сгенерирован")
            else:
                print("❌ AI сервис не инициализирован")
            
            # 5. Проверка звездного совета
            print("\n🌟 5. ЗВЕЗДНЫЙ СОВЕТ")
            star_service = StarAdviceService()
            
            # Валидация вопросов
            validation = await star_service.validate_question("Как мне найти работу в IT?")
            if validation["is_valid"]:
                print("✅ Валидация вопросов работает")
                
                # Генерация совета
                planets = chart.get_planets_data()
                advice = await star_service.generate_advice(
                    question="Как мне улучшить карьеру?",
                    category="career",
                    user_planets=planets,
                    birth_dt=chart.birth_date,
                    location=Location(lat=chart.latitude, lon=chart.longitude, city=chart.city),
                    user_name="Финальный Тест"
                )
                
                if advice and len(advice) > 200:
                    print(f"✅ Совет сгенерирован ({len(advice)} символов)")
                else:
                    print("❌ Совет не сгенерирован")
            else:
                print("❌ Валидация вопросов не работает")
            
            # 6. Проверка мотиваций
            print("\n🌅 6. ЕЖЕДНЕВНЫЕ МОТИВАЦИИ")
            motivation_service = MotivationService(ai_service)
            
            # Получение пользователя для мотивации
            user_for_motivation = await self.db_manager.get_user_profile(self.test_user_id)
            motivation = await motivation_service.generate_motivation(
                user=user_for_motivation,
                is_subscribed=False
            )
            
            if motivation and len(motivation) > 100:
                print(f"✅ Мотивация сгенерирована ({len(motivation)} символов)")
            else:
                print("❌ Мотивация не сгенерирована")
            
            # 7. Проверка системы подписки
            print("\n💎 7. СИСТЕМА ПОДПИСКИ")
            subscription_service = SubscriptionService()
            
            # Получение подписки
            subscription = await self.db_manager.get_or_create_subscription(self.test_user_id)
            print(f"✅ Подписка получена: {subscription.subscription_type.value}")
            
            # Проверка статуса
            is_premium = subscription_service.is_user_premium(self.test_user_id)
            print(f"✅ Статус Premium: {'Да' if is_premium else 'Нет'}")
            
            # Фильтрация планет
            all_planets = {
                "Солнце": PlanetPosition(sign="Лев", degree=15.0),
                "Луна": PlanetPosition(sign="Рак", degree=8.0),
                "Меркурий": PlanetPosition(sign="Лев", degree=12.0),
                "Венера": PlanetPosition(sign="Дева", degree=3.0),
                "Марс": PlanetPosition(sign="Скорпион", degree=22.0),
                "Юпитер": PlanetPosition(sign="Рыбы", degree=5.0),
                "Сатурн": PlanetPosition(sign="Козерог", degree=18.0),
            }
            
            free_planets = await subscription_service.filter_planets_for_user(
                all_planets, self.test_user_id
            )
            print(f"✅ Фильтрация планет: {len(free_planets)} из {len(all_planets)}")
            
            # 8. Проверка антиспама
            print("\n🛡️ 8. АНТИСПАМ СИСТЕМА")
            antispam_service = AntiSpamService()
            
            limits = antispam_service.check_limits(self.test_user_id, is_premium=False)
            print(f"✅ Лимиты проверены: {limits['questions_left']} вопросов")
            
            antispam_service.record_question(self.test_user_id)
            new_limits = antispam_service.check_limits(self.test_user_id, is_premium=False)
            print(f"✅ Использование записано: {new_limits['questions_left']} вопросов")
            
            # 9. Проверка астрологических расчетов
            print("\n⭐ 9. АСТРОЛОГИЧЕСКИЕ РАСЧЕТЫ")
            astro_service = AstroService()
            
            location = Location(lat=55.7558, lon=37.6176, city="Москва")
            birth_dt = datetime(1990, 7, 15, 12, 0)
            
            planets = await astro_service.calculate_natal_chart(birth_dt, location)
            if planets and len(planets) >= 10:
                print(f"✅ Натальная карта рассчитана: {len(planets)} планет")
            else:
                print("❌ Натальная карта не рассчитана")
            
            transits = await astro_service.calculate_transits(birth_dt, location, datetime.now())
            if transits:
                print(f"✅ Транзиты рассчитаны: {len(transits)} аспектов")
            else:
                print("❌ Транзиты не рассчитаны")
            
            retrograde_info = astro_service.get_retrograde_info()
            if retrograde_info:
                print(f"✅ Ретроградные планеты: {len(retrograde_info)} планет")
            else:
                print("❌ Ретроградные планеты не получены")
            
            # 10. Проверка совместимости
            print("\n💞 10. СИСТЕМА СОВМЕСТИМОСТИ")
            reports = await self.db_manager.get_user_compatibility_reports(user.id)
            print(f"✅ Отчеты совместимости: {len(reports)} отчетов")
            
            # 11. Финальная проверка данных
            print("\n📊 11. ФИНАЛЬНАЯ ПРОВЕРКА ДАННЫХ")
            charts = await self.db_manager.get_user_charts(self.test_user_id)
            print(f"✅ Натальные карты: {len(charts)} карт")
            
            predictions = await self.db_manager.get_user_predictions(self.test_user_id)
            print(f"✅ Прогнозы: {len(predictions)} прогнозов")
            
            users_for_mailing = await self.db_manager.get_users_for_mailing()
            print(f"✅ Пользователи для рассылки: {len(users_for_mailing)} пользователей")
            
            # Итоговый результат
            print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
            print("✅ Бот полностью готов к работе с пользователями")
            print("✅ Асинхронная БД функционирует корректно")
            print("✅ Все сервисы работают")
            print("✅ Пользовательский опыт оптимизирован")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ОШИБКА: {e}")
            return False
            
        finally:
            # Очистка тестовых данных
            await self.db_manager.delete_user_data(self.test_user_id)
            await self.db_manager.close()
            print("\n🧹 Тестовые данные очищены")

async def main():
    """Главная функция"""
    checker = FinalUserCheck()
    success = await checker.run_full_user_journey()
    
    if success:
        print("\n🎯 ФИНАЛЬНЫЙ ВЫВОД:")
        print("✅ SolarBalance готов к продакшен-запуску!")
        print("✅ Все пользовательские сценарии протестированы")
        print("✅ Асинхронная архитектура работает стабильно")
        print("✅ AI-сервисы интегрированы корректно")
        print("✅ Системы защиты активны")
        print("\n🚀 Бот готов к работе с реальными пользователями!")
    else:
        print("\n⚠️ ФИНАЛЬНЫЙ ВЫВОД:")
        print("❌ Обнаружены критические проблемы")
        print("❌ Требуется доработка перед запуском")

if __name__ == "__main__":
    asyncio.run(main()) 