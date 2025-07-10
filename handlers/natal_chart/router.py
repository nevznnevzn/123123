import asyncio
import logging
import time
from datetime import datetime

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from database import DatabaseManager
from keyboards import Keyboards
from models import Location
from services.astro_calculations import AstroService
from services.subscription_service import SubscriptionService
from states import AstroStates


def create_natal_chart_router(
    db_manager: DatabaseManager,
    astro_service: AstroService,
    subscription_service: SubscriptionService,
) -> Router:
    router = Router()

    def format_charts_count(count: int) -> str:
        """Правильное склонение слов в зависимости от количества натальных карт"""
        last_digit = count % 10
        last_two_digits = count % 100
        if 11 <= last_two_digits <= 14:
            return f"{count} сохраненных натальных карт"
        if last_digit == 1:
            return f"{count} сохраненная натальная карта"
        if 2 <= last_digit <= 4:
            return f"{count} сохраненные натальные карты"
        return f"{count} сохраненных натальных карт"

    @router.message(F.text.in_(["/natal", "📊 Натальные карты"]))
    async def natal_charts_menu(message: Message, state: FSMContext):
        """Меню для управления натальными картами"""
        await state.clear()
        user_id = message.from_user.id
        existing_charts = db_manager.get_user_charts(user_id)

        if existing_charts:
            text = f"🌟 <b>Натальные карты</b> ✨\n\n📊 У вас {format_charts_count(len(existing_charts))}.\n🔮 Вы можете просмотреть их, удалить или создать новую."
        else:
            text = "🌟 <b>Натальные карты</b> ✨\n\n🆕 У вас пока нет сохраненных натальных карт.\n💫 Создайте свою первую карту и узнайте тайны звезд!"

        await message.answer(
            text, reply_markup=Keyboards.natal_charts_list(existing_charts)
        )

    @router.callback_query(F.data == "select_chart_type")
    async def select_chart_type_handler(callback: CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "🌙 <b>Создание натальной карты</b> ⭐\n\nВыберите, для кого вы хотите составить натальную карту:",
            reply_markup=Keyboards.chart_type_selection(),
        )

    @router.callback_query(F.data.startswith("chart_type_"))
    async def process_chart_type(callback: CallbackQuery, state: FSMContext):
        """Обработка выбора типа карты"""
        chart_type = callback.data.split("_")[2]
        user_id = callback.from_user.id

        user, _ = db_manager.get_or_create_user(user_id, callback.from_user.full_name)

        # Проверка лимитов для бесплатных пользователей
        is_premium = subscription_service.is_user_premium(user_id)
        if not is_premium:
            existing_charts = db_manager.get_user_charts(user_id)
            if (
                len(existing_charts)
                >= subscription_service.FREE_USER_LIMITS["natal_charts"]
            ):
                await callback.answer(
                    "Вы достигли лимита на создание натальных карт (1).\n"
                    "Оформите Premium-подписку для снятия ограничений.",
                    show_alert=True,
                )
                return

        if chart_type == "own":
            user_profile = db_manager.get_user_profile(user_id)

            if not user_profile or not user_profile.is_profile_complete:
                await callback.answer(
                    "Сначала необходимо полностью настроить ваш профиль!",
                    show_alert=True,
                )
                return

            status_msg = await callback.message.edit_text(
                "✨ <b>Магия астрологии в действии...</b> 🔮\n\n⏳ Рассчитываю вашу натальную карту по данным профиля..."
            )

            location = astro_service.get_location(user_profile.birth_city)
            if not location:
                await status_msg.edit_text(
                    "Не удалось определить локацию из вашего профиля. Пожалуйста, проверьте настройки профиля."
                )
                return

            await create_chart_from_profile(
                callback, state, user_profile, location, status_msg
            )

        elif chart_type == "other":
            await callback.message.edit_text(
                "✍️ <b>Создание карты для другого человека</b>\n\n👤 Введите имя человека, для которого вы хотите составить карту:",
                reply_markup=None,
            )
            await state.set_state(AstroStates.waiting_for_other_name)

    async def create_chart_from_profile(
        callback: CallbackQuery, state: FSMContext, user_profile, location, status_msg
    ):
        """Создание натальной карты на основе профиля"""

        birth_dt = user_profile.birth_date
        has_warning = not user_profile.birth_time_specified
        planets_data = await astro_service.calculate_natal_chart(birth_dt, location)

        new_chart = db_manager.create_natal_chart(
            telegram_id=callback.from_user.id,
            name=f"Моя карта ({user_profile.name})",
            chart_type="own",
            birth_date=birth_dt,
            city=location.city,
            latitude=location.lat,
            longitude=location.lng,
            timezone=location.timezone,
            birth_time_specified=user_profile.birth_time_specified,
            has_warning=has_warning,
            planets_data=planets_data,
            chart_owner_name=user_profile.name,
        )

        await finish_calculation(
            callback.message,
            state,
            birth_dt,
            location,
            planets_data,
            status_msg,
            new_chart.id,
            has_warning,
        )

    @router.message(AstroStates.waiting_for_other_name)
    async def process_other_name(message: Message, state: FSMContext):
        """Обработка имени для чужой карты"""
        await state.update_data(other_name=message.text)
        await message.answer("Теперь введите город рождения этого человека:")
        await state.set_state(AstroStates.waiting_for_other_city)

    @router.message(AstroStates.waiting_for_other_city)
    async def process_other_city(message: Message, state: FSMContext):
        """Обработка города для чужой карты"""
        city = message.text.strip()
        
        # Сначала проверяем валидность ввода
        is_valid, error_message = astro_service.validate_city_input(city)
        if not is_valid:
            await message.answer(
                f"❌ <b>Ошибка ввода:</b> {error_message}\n\n"
                "💡 <b>Примеры правильного ввода:</b>\n"
                "• Москва\n"
                "• Санкт-Петербург\n"
                "• Екатеринбург\n"
                "• Нью-Йорк\n\n"
                "Попробуйте еще раз:",
                reply_markup=Keyboards.skip_step_keyboard(),
            )
            return
        
        # Если валидация прошла, пробуем найти город
        location = astro_service.get_location(city)

        if location is None:
            await message.answer(
                "🌍 <b>Город не найден</b>\n\n"
                "Не удалось найти указанный город. Проверьте правильность написания.\n\n"
                "💡 <b>Попробуйте:</b>\n"
                "• Указать полное название (например, 'Ростов-на-Дону')\n"
                "• Добавить страну (например, 'Париж, Франция')\n"
                "• Проверить правильность написания\n\n"
                "Введите название города еще раз:",
                reply_markup=Keyboards.skip_step_keyboard(),
            )
            return

        await state.update_data(other_location=location)
        await message.answer(
            f"📍 Город: {location.city} (Таймзона: {location.timezone})\n"
            "Теперь введите дату и время рождения в формате: <b>ДД.ММ.ГГГГ ЧЧ:ММ</b>",
            reply_markup=Keyboards.skip_step_keyboard(),
        )
        await state.set_state(AstroStates.waiting_for_other_birth_date)

    @router.message(AstroStates.waiting_for_other_birth_date)
    async def process_other_birth_date(message: Message, state: FSMContext):
        """Обработка даты и времени для чужой карты"""
        try:
            birth_dt = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
            await state.update_data(other_birth_dt=birth_dt, birth_time_specified=True)

            status_msg = await message.answer(
                "✨ Рассчитываю натальную карту...", reply_markup=ReplyKeyboardRemove()
            )
            user_data = await state.get_data()
            location = user_data["other_location"]
            other_name = user_data["other_name"]

            await complete_other_calculation(
                message,
                state,
                birth_dt,
                location,
                status_msg,
                other_name,
                has_warning=False,
            )

        except ValueError:
            await message.answer(
                "😕 Неверный формат. Пожалуйста, введите дату и время в формате: <b>ДД.ММ.ГГГГ ЧЧ:ММ</b>.",
                reply_markup=Keyboards.skip_step_keyboard(),
            )

    async def complete_other_calculation(
        message: Message,
        state: FSMContext,
        birth_dt,
        location,
        status_msg,
        other_name,
        has_warning=False,
    ):
        """Завершение расчета для чужой карты"""
        planets_data = await astro_service.calculate_natal_chart(birth_dt, location)

        new_chart = db_manager.create_natal_chart(
            telegram_id=message.from_user.id,
            name=f"Карта для {other_name}",
            chart_type="other",
            birth_date=birth_dt,
            city=location.city,
            latitude=location.lat,
            longitude=location.lng,
            timezone=location.timezone,
            birth_time_specified=not has_warning,
            has_warning=has_warning,
            planets_data=planets_data,
            chart_owner_name=other_name,
        )

        await finish_calculation(
            message,
            state,
            birth_dt,
            location,
            planets_data,
            status_msg,
            new_chart.id,
            has_warning,
        )

    async def finish_calculation(
        message: Message,
        state: FSMContext,
        birth_dt,
        location,
        planets_data,
        status_msg,
        chart_id: int,
        has_warning=False,
    ):
        """Отображение результатов расчета"""
        birth_date_str = birth_dt.strftime("%d.%m.%Y")
        birth_time_str = birth_dt.strftime("%H:%M")

        if birth_time_str == "12:00" or has_warning:
            time_info = "⚠️ (время неточное, используется 12:00)"
        else:
            time_info = ""

        user_id = message.chat.id
        is_premium = subscription_service.is_user_premium(user_id)
        available_planets = subscription_service.filter_planets_for_user(
            planets_data, user_id
        )

        base_text = (
            f"✨ <b>Натальная карта готова!</b> 🌟\n\n"
            f"🗓️ <b>Дата и время:</b> {birth_date_str} {birth_time_str} {time_info}\n"
            f"📍 <b>Место:</b> {location.city}\n\n"
            "🪐 <b>Планеты в вашей карте:</b>\n"
            "👆 Нажмите на планету, чтобы узнать ее значение:"
        )

        if not is_premium and len(available_planets) < len(planets_data):
            premium_text = f"\n\n💎 <b>Premium подписка</b> откроет анализ всех {len(planets_data)} планет!"
            text = base_text + premium_text
        else:
            text = base_text

        try:
            await status_msg.edit_text(
                text,
                reply_markup=Keyboards.planets(
                    list(available_planets.keys()), chart_id, is_premium=is_premium
                ),
            )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                logging.info("Сообщение не изменено, пропуск редактирования.")
            else:
                raise

        if state:
            await state.clear()

    @router.callback_query(F.data.startswith("planet_"))
    async def planet_callback(callback: CallbackQuery):
        """Обработка нажатия на кнопку планеты"""
        try:
            _, chart_id, planet_name = callback.data.split("_")
            chart_id = int(chart_id)
        except ValueError:
            await callback.answer("Ошибка! Неверные данные.", show_alert=True)
            return

        await callback.answer()

        user_id = callback.from_user.id
        chart = db_manager.get_chart_by_id(chart_id, user_id)

        if not chart:
            await callback.message.edit_text(
                "Карта не найдена!", reply_markup=Keyboards.back_to_main_menu()
            )
            return

        planets_data = chart.get_planets_data()
        planet_info = planets_data.get(planet_name)

        if not planet_info:
            await callback.message.answer(
                f"Информация о планете '{planet_name}' не найдена.", show_alert=True
            )
            return

        sign = planet_info.sign
        description = astro_service.get_planet_description(planet_name, sign)

        planet_emoji = {
            "Солнце": "☀️",
            "Луна": "🌙",
            "Меркурий": "☿️",
            "Венера": "♀️",
            "Марс": "♂️",
            "Юпитер": "♃",
            "Сатурн": "♄",
            "Уран": "♅",
            "Нептун": "♆",
            "Плутон": "♇",
            "Асцендент": "⬆️",
        }.get(planet_name, "🪐")

        text = f"{planet_emoji} <b>{planet_name} в знаке {sign}</b> ✨\n\n{description}"

        await callback.message.edit_text(
            text, reply_markup=Keyboards.back_to_planets(chart_id)
        )

    @router.callback_query(
        F.data.startswith("chart_") & ~F.data.startswith("chart_type_")
    )
    async def chart_selected(callback: CallbackQuery):
        """Обработчик выбора конкретной карты из списка"""
        chart_id = int(callback.data.split("_")[1])
        user_id = callback.from_user.id
        chart = db_manager.get_chart_by_id(chart_id, user_id)

        if not chart:
            await callback.answer("Карта не найдена!", show_alert=True)
            return

        chart_name = (
            f"👤 Ваша карта ({chart.city})"
            if chart.chart_type == "own"
            else f"👥 Карта для {chart.chart_owner_name} ({chart.city})"
        )

        birth_date_str = chart.birth_date.strftime("%d.%m.%Y")
        text = f"Выбрана карта: <b>{chart_name}</b> от {birth_date_str}. Что вы хотите сделать?"

        await callback.message.edit_text(
            text, reply_markup=Keyboards.chart_actions(chart_id)
        )

    @router.callback_query(F.data.startswith("open_chart_"))
    async def open_chart(callback: CallbackQuery):
        """Открытие (отображение) существующей натальной карты"""
        chart_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        chart = db_manager.get_chart_by_id(chart_id, user_id)

        if not chart:
            await callback.answer("Карта не найдена!", show_alert=True)
            return

        planets_data = chart.get_planets_data()
        birth_dt = chart.birth_date
        location = Location(
            city=chart.city,
            lat=chart.latitude,
            lng=chart.longitude,
            timezone=chart.timezone,
        )

        await finish_calculation(
            callback.message,
            None,
            birth_dt,
            location,
            planets_data,
            callback.message,
            chart.id,
            chart.has_warning,
        )

    @router.callback_query(F.data.startswith("delete_chart_"))
    async def delete_chart(callback: CallbackQuery):
        """Запрос подтверждения на удаление карты"""
        chart_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        chart = db_manager.get_chart_by_id(chart_id, user_id)

        if not chart:
            await callback.answer("Карта не найдена!", show_alert=True)
            return

        # Формируем название карты на основе её данных
        if chart.chart_type == "own":
            chart_name = f"Ваша карта ({chart.city})"
        else:
            owner_name = chart.chart_owner_name or "Неизвестно"
            chart_name = f"Карта для {owner_name} ({chart.city})"

        await callback.message.edit_text(
            f"Вы уверены, что хотите удалить карту '<b>{chart_name}</b>'?",
            reply_markup=Keyboards.confirm_delete(chart_id),
        )

    @router.callback_query(F.data.startswith("confirm_delete_chart_"))
    async def confirm_delete_chart(callback: CallbackQuery):
        """Подтверждение удаления карты"""
        try:
            chart_id = int(callback.data.split("_")[3])
            user_id = callback.from_user.id
            chart = db_manager.get_chart_by_id(chart_id, user_id)
            if chart:
                chart_name = (
                    f"карта для {chart.chart_owner_name}"
                    if chart.chart_type == "other"
                    else "ваша карта"
                )
                success = db_manager.delete_natal_chart(chart_id, user_id)
                text = (
                    f"✅ Успешно удалена {chart_name}."
                    if success
                    else "😕 Не удалось удалить карту."
                )
            else:
                text = "Карта уже была удалена."

            existing_charts = db_manager.get_user_charts(user_id)
            await callback.message.edit_text(
                f"{text}\n\n🔮 Меню натальных карт",
                reply_markup=Keyboards.natal_charts_list(existing_charts),
            )
        except ValueError:
            await callback.answer("Ошибка! Неверный ID карты.", show_alert=True)

    @router.callback_query(F.data == "back_to_charts_list")
    async def back_to_charts_list_callback(callback: CallbackQuery, state: FSMContext):
        """Возврат к списку натальных карт"""
        await natal_charts_menu(callback.message, state)
        await callback.answer()

    return router
