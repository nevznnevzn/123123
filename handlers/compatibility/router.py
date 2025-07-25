from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from database_async import async_db_manager
from keyboards import Keyboards
from services.ai_predictions import AIPredictionService
from services.astro_calculations import AstroService
from states import AstroStates

router = Router()
astro_service = AstroService()
ai_service = AIPredictionService()


@router.message(F.text == "💞 Совместимость")
async def compatibility_start(message: Message, state: FSMContext):
    """Меню совместимости: показывает список отчетов или предлагает создать первый."""
    await state.clear()
    user = await async_db_manager.get_user_profile(message.from_user.id)

    if not user or not user.is_profile_complete:
        await message.answer(
            "Для расчета совместимости сначала нужно заполнить ваш профиль.",
            reply_markup=Keyboards.setup_profile(),
        )
        return

    reports = await async_db_manager.get_user_compatibility_reports(user.id)

    if not reports:
        text = "💕 <b>Астрологическая совместимость</b> ✨\n\n💫 У вас пока нет сохраненных отчетов.\n🌹 Хотите создать первый?"
    else:
        text = f"💕 <b>Астрологическая совместимость</b> ✨\n\n📊 У вас {len(reports)} сохраненных отчетов.\n💖 Выберите отчет для просмотра или создайте новый."

    await message.answer(
        text, reply_markup=Keyboards.compatibility_reports_list(reports)
    )


@router.callback_query(F.data == "new_compatibility_report")
async def start_new_report_calculation(callback: CallbackQuery, state: FSMContext):
    """Начало создания нового отчета о совместимости."""
    await callback.message.edit_text(
        "💕 <b>Создание отчета о совместимости</b> ✨\n\n👤 Чтобы начать, введите имя вашего партнера.",
        reply_markup=None,
    )
    await state.set_state(AstroStates.waiting_for_partner_name)


@router.message(AstroStates.waiting_for_partner_name)
async def process_partner_name(message: Message, state: FSMContext):
    """Обработка имени партнера"""
    await state.update_data(partner_name=message.text)
    await message.answer(
        "🌍 <b>Город рождения партнера</b>\n\n📍 Теперь введите город рождения партнера."
    )
    await state.set_state(AstroStates.waiting_for_partner_city)


@router.message(AstroStates.waiting_for_partner_city)
async def process_partner_city(message: Message, state: FSMContext):
    """Обработка города рождения партнера"""
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
            "🌍 <b>Город партнера не найден</b>\n\n"
            "Не удалось найти указанный город. Проверьте правильность написания.\n\n"
            "💡 <b>Попробуйте:</b>\n"
            "• Указать полное название (например, 'Ростов-на-Дону')\n"
            "• Добавить страну (например, 'Париж, Франция')\n"
            "• Проверить правильность написания\n\n"
            "Введите город рождения партнера еще раз:"
        )
        return

    await state.update_data(partner_location=location)

    await message.answer(
        f"✅ <b>Город партнера:</b> {location.city} 📍\n\n"
        "🗓️ <b>Дата и время рождения</b>\n\n"
        "Теперь введите его дату и время рождения в формате: <b>ДД.ММ.ГГГГ ЧЧ:ММ</b>",
        reply_markup=Keyboards.skip_step_keyboard(),
    )
    await state.set_state(AstroStates.waiting_for_partner_birth_date)


@router.message(AstroStates.waiting_for_partner_birth_date)
async def process_partner_birth_date(message: Message, state: FSMContext):
    """Обработка времени рождения партнера"""
    birth_dt_str = message.text

    if birth_dt_str == "Пропустить шаг (время будет 12:00)":
        await message.answer(
            "Пожалуйста, сначала введите дату в формате <b>ДД.ММ.ГГГГ</b>, а затем сможете пропустить ввод времени."
        )
        return

    try:
        birth_dt = datetime.strptime(birth_dt_str, "%d.%m.%Y %H:%M")
    except ValueError:
        # Попробуем разобрать только дату, если время не указано
        try:
            birth_dt = datetime.strptime(f"{birth_dt_str} 12:00", "%d.%m.%Y %H:%M")
        except ValueError:
            await message.answer(
                "😕 Неверный формат. Пожалуйста, введите дату и время в формате <b>ДД.ММ.ГГГГ ЧЧ:ММ</b> (например, 25.10.1995 18:45) или только дату.",
                reply_markup=Keyboards.skip_step_keyboard(),
            )
            return

    await state.update_data(partner_birth_dt=birth_dt)

    await message.answer(
        "✨ <b>Все данные собраны!</b> 💫\n\n🔮 Какую сферу жизни вы хотите проверить?",
        reply_markup=Keyboards.compatibility_spheres(),
    )
    await state.set_state(AstroStates.waiting_for_compatibility_sphere)


@router.callback_query(
    AstroStates.waiting_for_compatibility_sphere, F.data.startswith("comp_sphere_")
)
async def process_compatibility_sphere(callback: CallbackQuery, state: FSMContext):
    """Финальный шаг: генерация и сохранение отчета по совместимости"""
    sphere = callback.data.split("_")[2]

    await callback.message.edit_text(
        "⏳ <b>Звезды анализируют совместимость...</b> 💕\n\n✨ Это может занять до 45 секунд."
    )

    user_profile = await async_db_manager.get_user_profile(callback.from_user.id)
    partner_data = await state.get_data()

    # Рассчитываем планеты для пользователя и партнера
    user_location = astro_service.get_location(user_profile.birth_city)
    user_planets = await astro_service.calculate_natal_chart(
        user_profile.birth_date, user_location
    )
    partner_location = partner_data.get("partner_location")
    partner_birth_dt = partner_data.get("partner_birth_dt")
    partner_planets = await astro_service.calculate_natal_chart(
        partner_birth_dt, partner_location
    )

    if not user_planets or not partner_planets:
        await callback.message.edit_text(
            "😕 Не удалось рассчитать астрологические данные. Попробуйте снова."
        )
        await state.clear()
        return

    # Получаем отчет от AI
    report_text = await ai_service.generate_compatibility_report(
        user_planets=user_planets,
        partner_planets=partner_planets,
        sphere=sphere,
        user_name=user_profile.name,
        partner_name=partner_data.get("partner_name"),
    )

    # Если генерация не удалась
    if not report_text:
        reports = await async_db_manager.get_user_compatibility_reports(user_profile.id)
        await callback.message.edit_text(
            "К сожалению, не удалось сгенерировать отчет. Попробуйте позже.",
            reply_markup=Keyboards.compatibility_reports_list(reports),
        )
        await state.clear()
        return

    # Проверяем длину отчета и обрезаем при необходимости
    if len(report_text) > 3800:  # Увеличиваем лимит для более подробных отчетов
        # Обрезаем по последнему полному предложению
        truncated = report_text[:3797]
        last_sentence = truncated.rfind('.')
        if last_sentence > 3000:  # Если есть точка в разумном месте
            report_text = truncated[:last_sentence + 1] + "\n\n<i>...</i>"
        else:
            report_text = truncated + "..."

    # Сохраняем отчет в БД
    saved_report = await async_db_manager.save_compatibility_report(
        user_id=user_profile.id,
        user_name=user_profile.name,
        partner_name=partner_data.get("partner_name"),
        user_birth_date=user_profile.birth_date,
        partner_birth_date=partner_birth_dt,
        sphere=sphere,
        report_text=report_text,
    )

    await callback.message.edit_text(
        report_text,
        reply_markup=Keyboards.compatibility_report_actions(saved_report.id),
    )
    await state.clear()


@router.callback_query(F.data.startswith("view_comp_report_"))
async def view_compatibility_report(callback: CallbackQuery):
    """Просмотр сохраненного отчета о совместимости."""
    report_id = int(callback.data.split("_")[3])
    user_profile = await async_db_manager.get_user_profile(callback.from_user.id)
    user_id = user_profile.id
    report = await async_db_manager.get_compatibility_report_by_id(report_id, user_id)

    if report:
        report_text = report.report_text

        # Проверяем длину отчета и обрезаем при необходимости (для старых отчетов)
        if len(report_text) > 3800:  # Увеличиваем лимит для более подробных отчетов
            # Обрезаем по последнему полному предложению
            truncated = report_text[:3797]
            last_sentence = truncated.rfind('.')
            if last_sentence > 3000:  # Если есть точка в разумном месте
                report_text = truncated[:last_sentence + 1] + "\n\n<i>...</i>"
            else:
                report_text = truncated + "..."

        await callback.message.edit_text(
            report_text, reply_markup=Keyboards.compatibility_report_actions(report.id)
        )
    else:
        await callback.answer("Отчет не найден.", show_alert=True)


@router.callback_query(F.data.startswith("delete_comp_report_"))
async def delete_compatibility_report(callback: CallbackQuery):
    """Запрос на удаление отчета о совместимости."""
    report_id = int(callback.data.split("_")[3])
    await callback.message.edit_text(
        "Вы уверены, что хотите удалить этот отчет?",
        reply_markup=Keyboards.confirm_delete_compatibility_report(report_id),
    )


@router.callback_query(F.data.startswith("confirm_delete_comp_report_"))
async def confirm_delete_compatibility_report(callback: CallbackQuery):
    """Подтверждение удаления отчета и возврат к списку."""
    report_id = int(callback.data.split("_")[4])
    user = await async_db_manager.get_user_profile(callback.from_user.id)

    success = await async_db_manager.delete_compatibility_report(report_id, user.id)
    if success:
        await callback.answer("Отчет удален.", show_alert=True)
    else:
        await callback.answer("Не удалось удалить отчет.", show_alert=True)

    # Обновляем список отчетов
    reports = await async_db_manager.get_user_compatibility_reports(user.id)

    if not reports:
        text = "💕 <b>Астрологическая совместимость</b> ✨\n\n💫 У вас пока нет сохраненных отчетов.\n🌹 Хотите создать первый?"
    else:
        text = f"💕 <b>Астрологическая совместимость</b> ✨\n\n📊 У вас {len(reports)} сохраненных отчетов.\n💖 Выберите отчет для просмотра или создайте новый."

    await callback.message.edit_text(
        text, reply_markup=Keyboards.compatibility_reports_list(reports)
    )


@router.callback_query(F.data == "back_to_comp_reports")
async def back_to_comp_reports_list(callback: CallbackQuery):
    """Возврат к списку отчетов о совместимости."""
    user = await async_db_manager.get_user_profile(callback.from_user.id)
    reports = await async_db_manager.get_user_compatibility_reports(user.id)

    if not reports:
        text = "💕 <b>Астрологическая совместимость</b> ✨\n\n💫 У вас пока нет сохраненных отчетов.\n🌹 Хотите создать первый?"
    else:
        text = f"💕 <b>Астрологическая совместимость</b> ✨\n\n📊 У вас {len(reports)} сохраненных отчетов.\n💖 Выберите отчет для просмотра или создайте новый."

    # Проверяем, отличается ли новый текст от текущего
    if callback.message.text != text:
        await callback.message.edit_text(
            text, reply_markup=Keyboards.compatibility_reports_list(reports)
        )
    else:
        # Если текст одинаковый, просто отвечаем на callback без изменения сообщения
        await callback.answer()
