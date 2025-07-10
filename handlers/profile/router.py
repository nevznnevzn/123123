from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from database import DatabaseManager
from keyboards import Keyboards
from services.astro_calculations import AstroService
from states import AstroStates, ProfileStates
from utils import format_period_info, get_next_available_time, get_prediction_period

# Убираем создание зависимостей на уровне модуля
# astro_service = AstroService()


def create_profile_router(
    db_manager: DatabaseManager, astro_service: AstroService
) -> Router:
    router = Router()

    @router.message(F.text == "⚙️ Настроить профиль")
    async def setup_profile_start(message: Message, state: FSMContext):
        """Начало настройки профиля"""
        await state.clear()
        await message.answer(
            "👤 <b>Настройка профиля - Шаг 1 из 4</b>\n\nКак вас зовут? Введите ваше имя:",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(ProfileStates.waiting_for_name)

    @router.message(ProfileStates.waiting_for_name)
    async def process_name(message: Message, state: FSMContext):
        """Обработка имени для профиля"""
        name = message.text
        if len(name) > 30:
            await message.answer("Имя слишком длинное, попробуйте еще раз.")
            return
        await state.update_data(name=name)
        await message.answer(
            "👤 <b>Настройка профиля - Шаг 2 из 4</b>\n\nВыберите ваш пол:",
            reply_markup=Keyboards.gender_selection(),
        )
        await state.set_state(ProfileStates.waiting_for_gender)

    @router.callback_query(
        ProfileStates.waiting_for_gender, F.data.in_(["gender_male", "gender_female"])
    )
    async def process_gender(callback: CallbackQuery, state: FSMContext):
        """Обработка выбора пола"""
        gender = callback.data.split("_")[1]
        await state.update_data(gender=gender)
        await callback.message.edit_text(
            "👤 <b>Настройка профиля - Шаг 3 из 4</b>\n\nВведите ваш город рождения:",
            reply_markup=None,
        )
        await state.set_state(ProfileStates.waiting_for_city)

    @router.message(ProfileStates.waiting_for_city)
    async def process_city(message: Message, state: FSMContext):
        """Обработка города рождения для профиля"""
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
                "Попробуйте еще раз:"
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
                "Введите название города еще раз:"
            )
            return

        await state.update_data(city=city, location=location)
        await message.answer(
            "📅 <b>Настройка профиля - Шаг 4 из 4</b>\n\n"
            "Введите дату и время вашего рождения в одном из форматов:\n\n"
            "🔸 15.03.1990 14:30\n"
            "🔸 15/03/1990 14:30\n"
            "🔸 1990-03-15 14:30\n"
            "🔸 15.03.1990 (без времени)\n\n"
            "💡 Для точного расчета натальной карты важно указать время!",
            parse_mode="HTML",
        )
        await state.set_state(ProfileStates.waiting_for_birth_date)

    @router.message(ProfileStates.waiting_for_birth_date)
    async def process_birth_date(message: Message, state: FSMContext):
        """Обработка даты и времени рождения для профиля"""
        try:
            # Сначала пробуем полный формат
            birth_dt = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        except ValueError:
            try:
                # Затем пробуем только дату, время по умолчанию 12:00
                birth_dt = datetime.strptime(f"{message.text} 12:00", "%d.%m.%Y %H:%M")
            except ValueError:
                await message.answer(
                    "😕 Неверный формат. Пожалуйста, введите дату и время в формате: <b>ДД.ММ.ГГГГ ЧЧ:ММ</b>.\n"
                    "Например: 23.08.1990 14:30. Вы также можете ввести только дату.",
                    reply_markup=Keyboards.skip_step_keyboard(),
                )
                return

        await state.update_data(birth_date=birth_dt)

        user_data = await state.get_data()

        # Сохраняем или обновляем профиль
        db_manager.update_user_profile(
            telegram_id=message.from_user.id,
            name=user_data["name"],
            gender=user_data["gender"],
            birth_date=birth_dt,
            birth_year=birth_dt.year,
            birth_city=user_data["city"],
            birth_time_specified=not ("12:00" in birth_dt.strftime("%H:%M")),
        )

        gender_map = {"male": "Мужской", "female": "Женский"}

        await message.answer(
            "✨ <b>Профиль успешно настроен!</b> 🎉\n\n"
            f"👤 <b>Имя:</b> {user_data['name']}\n"
            f"⚤ <b>Пол:</b> {gender_map.get(user_data['gender'], 'Не указан')}\n"
            f"🏙️ <b>Город рождения:</b> {user_data['city'].capitalize()}\n"
            f"🗓️ <b>Дата рождения:</b> {birth_dt.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=Keyboards.main_menu(),
        )
        await message.answer(
            "🎉 <b>Отлично!</b> ✨\n\n🔮 Теперь вы можете создавать натальные карты и получать персональные прогнозы!",
            reply_markup=None,
        )
        await state.clear()

    @router.message(F.text == "👤 Профиль")
    async def show_profile(message: Message):
        """Отображение профиля пользователя"""
        user_id = message.from_user.id
        user_profile = db_manager.get_user_profile(user_id)

        if user_profile and user_profile.is_profile_complete:
            birth_date_str = (
                user_profile.birth_date.strftime("%d.%m.%Y")
                if user_profile.birth_date
                else "Не указана"
            )
            birth_time_str = (
                user_profile.birth_date.strftime("%H:%M")
                if user_profile.birth_date and user_profile.birth_time_specified
                else "Не указано"
            )
            gender_str = "Мужской" if user_profile.gender == "male" else "Женский"

            profile_text = (
                f"<b>👤 Ваш профиль:</b>\n\n"
                f"<b>Имя:</b> {user_profile.name}\n"
                f"<b>Пол:</b> {gender_str}\n"
                f"<b>Дата рождения:</b> {birth_date_str}\n"
                f"<b>Время рождения:</b> {birth_time_str}\n"
                f"<b>Город рождения:</b> {user_profile.birth_city}"
            )
            await message.answer(
                profile_text,
                reply_markup=Keyboards.profile_menu(
                    notifications_enabled=user_profile.notifications_enabled
                ),
            )
        else:
            await message.answer(
                "Профиль не найден или не заполнен. Пожалуйста, настройте его.",
                reply_markup=Keyboards.setup_profile(),
            )

    @router.callback_query(F.data == "toggle_notifications")
    async def toggle_notifications_handler(callback: CallbackQuery):
        """Переключает статус уведомлений"""
        user_id = callback.from_user.id
        user = db_manager.get_user_profile(user_id)

        if not user:
            await callback.answer("Профиль не найден.", show_alert=True)
            return

        # Инвертируем текущий статус
        new_status = not user.notifications_enabled
        db_manager.set_notifications(user_id, new_status)

        # Обновляем клавиатуру в сообщении
        await callback.message.edit_reply_markup(
            reply_markup=Keyboards.profile_menu(notifications_enabled=new_status)
        )

        status_text = "включены" if new_status else "выключены"
        await callback.answer(f"Ежедневные уведомления {status_text}.")

    @router.callback_query(F.data == "edit_profile")
    async def edit_profile_callback(callback: CallbackQuery, state: FSMContext):
        """Начало редактирования профиля"""
        await callback.message.edit_text("Пожалуйста, введите ваше новое имя:")
        await state.set_state(ProfileStates.waiting_for_name)

    return router
