import logging
from datetime import datetime
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from database_async import async_db_manager
from keyboards import Keyboards
from services.astro_calculations import AstroService
from services.sky_visualization_service import SkyVisualizationService

from .keyboards import SkyMapKeyboards
from .states import SkyMapStates

logger = logging.getLogger(__name__)

router = Router()

# Инициализируем сервисы
sky_service = SkyVisualizationService()
astro_service = AstroService()


@router.message(F.text == "🌌 Звёздное небо")
async def sky_map_start(message: Message, state: FSMContext):
    """Главное меню звездного неба"""
    await state.clear()
    user_id = message.from_user.id

    # Проверяем заполнен ли профиль
    user_profile = await async_db_manager.get_user_profile(user_id)
    if not user_profile or not user_profile.is_profile_complete:
        await message.answer(
            "🌌 <b>Звёздное небо</b> ✨\n\n"
            "Для создания карты звездного неба необходимо заполнить профиль.",
            reply_markup=SkyMapKeyboards.back_to_main(),
        )
        return

    text = (
        "🌌 <b>Звёздное небо</b> ✨\n\n"
        "В ту секунду, когда ты появился(лась) на свет, небо замерло — "
        "и выстроилось в уникальный узор. Планеты, звёзды, Луна — "
        "всё сложилось в космический отпечаток, который принадлежит только тебе.\n\n"
        "✨ Готов(а) увидеть, как выглядело твоё небо?"
    )

    await message.answer(text, reply_markup=SkyMapKeyboards.main_menu())


@router.callback_query(F.data == "my_sky")
async def create_my_sky(callback: CallbackQuery, state: FSMContext):
    """Создание карты неба пользователя"""
    user_id = callback.from_user.id

    # Получаем профиль пользователя
    user_profile = await async_db_manager.get_user_profile(user_id)
    if not user_profile or not user_profile.is_profile_complete:
        await callback.answer("Необходимо заполнить профиль", show_alert=True)
        return

    # Показываем статус обработки
    processing_msg = await callback.message.edit_text(
        "🌌 <b>Создание карты звездного неба...</b> ✨\n\n"
        "⏳ Рассчитываем позиции планет и звезд...\n"
        "🔭 Это может занять до 30 секунд"
    )

    try:
        # Получаем данные пользователя
        location = astro_service.get_location(user_profile.birth_city)
        if not location:
            await callback.message.edit_text(
                "❌ Не удалось определить координаты города рождения.\n"
                "Проверьте корректность данных в профиле.",
                reply_markup=SkyMapKeyboards.back_to_main(),
            )
            return

        # Рассчитываем натальную карту
        planets = await astro_service.calculate_natal_chart(user_profile.birth_date, location)
        if not planets:
            await callback.message.edit_text(
                "❌ Не удалось рассчитать натальную карту.\n"
                "Проверьте корректность данных в профиле.",
                reply_markup=SkyMapKeyboards.back_to_main(),
            )
            return

        # Создаем карту неба
        sky_image_bytes = await sky_service.create_birth_sky_map(
            birth_date=user_profile.birth_date,
            location=location,
            planets=planets,
            owner_name=user_profile.name,
        )

        if not sky_image_bytes:
            await callback.message.edit_text(
                "❌ Не удалось создать карту звездного неба.\n" "Попробуйте позже.",
                reply_markup=SkyMapKeyboards.back_to_main(),
            )
            return

        # Формируем персонализированное описание
        luna_sign = planets.get('Луна', type('obj', (), {'sign': 'неизвестного знака'})).sign
        solnce_sign = planets.get('Солнце', type('obj', (), {'sign': 'неизвестного знака'})).sign
        
        description = (
            f"🌌 <b>Твоё звездное небо</b> ✨\n\n"
            f"🪐 <i>Так выглядело небо, когда ты родился(лась) "
            f"{user_profile.birth_date.strftime('%d %B %Y')} в {user_profile.birth_date.strftime('%H:%M')} "
            f"в {user_profile.birth_city}</i>\n\n"
            f"🌙 Луна только вышла из {luna_sign}, а Солнце в {solnce_sign} взошло над горизонтом — "
            f"момент тёплой силы и уникальной космической энергии...\n\n"
            f"✨ <i>Этот узор звезд и планет принадлежит только тебе!</i>"
        )

        # Отправляем изображение
        image_file = BufferedInputFile(sky_image_bytes, filename="star_map.png")
        await callback.message.answer_photo(
            photo=image_file,
            caption=description,
            reply_markup=SkyMapKeyboards.sky_actions(),
        )

        # Удаляем сообщение о статусе
        await callback.message.delete()

    except Exception as e:
        logger.error(f"Ошибка создания карты неба: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании карты звездного неба.\n"
            "Пожалуйста, попробуйте позже.",
            reply_markup=SkyMapKeyboards.back_to_main(),
        )


@router.callback_query(F.data == "other_sky")
async def start_other_sky(callback: CallbackQuery, state: FSMContext):
    """Начало создания карты неба для другого человека"""
    await callback.message.edit_text(
        "🌌 <b>Небо другого человека</b> ✨\n\n"
        "Введите имя человека, для которого хотите создать карту звездного неба:",
        reply_markup=SkyMapKeyboards.back_to_main(),
    )
    await state.set_state(SkyMapStates.waiting_for_other_name)


@router.message(SkyMapStates.waiting_for_other_name)
async def process_other_name(message: Message, state: FSMContext):
    """Обработка имени для чужой карты"""
    other_name = message.text.strip()

    if len(other_name) > 50:
        await message.answer(
            "Имя слишком длинное. Пожалуйста, введите более короткое имя."
        )
        return

    await state.update_data(other_name=other_name)
    await message.answer(
        f"👤 <b>Карта для {other_name}</b>\n\n"
        "📅 Введите дату рождения в формате ДД.ММ.ГГГГ:\n"
        "Например: <code>25.12.1990</code>",
        reply_markup=SkyMapKeyboards.back_to_main(),
    )
    await state.set_state(SkyMapStates.waiting_for_other_date)


@router.message(SkyMapStates.waiting_for_other_date)
async def process_other_date(message: Message, state: FSMContext):
    """Обработка даты рождения для чужой карты"""
    try:
        # Пробуем разные форматы даты
        date_formats = ["%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]
        birth_date = None

        for date_format in date_formats:
            try:
                birth_date = datetime.strptime(message.text.strip(), date_format)
                break
            except ValueError:
                continue

        if not birth_date:
            await message.answer(
                "❌ Неверный формат даты.\n\n"
                "Пожалуйста, введите дату в формате <b>ДД.ММ.ГГГГ</b>\n"
                "Например: <code>25.12.1990</code>",
                reply_markup=SkyMapKeyboards.back_to_main(),
            )
            return

        await state.update_data(birth_date=birth_date)
        await message.answer(
            "🕐 <b>Время рождения</b>\n\n"
            "Введите время рождения в формате ЧЧ:ММ:\n"
            "Например: <code>14:30</code>\n\n"
            "💡 Если точное время неизвестно, можете ввести <code>12:00</code>",
            reply_markup=SkyMapKeyboards.skip_time(),
        )
        await state.set_state(SkyMapStates.waiting_for_other_time)

    except Exception as e:
        logger.error(f"Ошибка обработки даты: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке даты. Попробуйте еще раз.",
            reply_markup=SkyMapKeyboards.back_to_main(),
        )


@router.message(SkyMapStates.waiting_for_other_time)
async def process_other_time(message: Message, state: FSMContext):
    """Обработка времени рождения для чужой карты"""
    try:
        time_str = message.text.strip()

        # Пробуем парсить время
        try:
            time_parts = time_str.split(":")
            hours = int(time_parts[0])
            minutes = int(time_parts[1]) if len(time_parts) > 1 else 0

            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError("Invalid time range")

        except (ValueError, IndexError):
            await message.answer(
                "❌ Неверный формат времени.\n\n"
                "Пожалуйста, введите время в формате <b>ЧЧ:ММ</b>\n"
                "Например: <code>14:30</code> или <code>9:15</code>",
                reply_markup=SkyMapKeyboards.skip_time(),
            )
            return

        # Объединяем дату и время
        state_data = await state.get_data()
        birth_date = state_data["birth_date"]
        birth_datetime = birth_date.replace(hour=hours, minute=minutes)

        await state.update_data(birth_datetime=birth_datetime)
        await message.answer(
            "🏙️ <b>Место рождения</b>\n\n"
            "Введите город рождения:\n"
            "Например: <code>Москва</code> или <code>Санкт-Петербург</code>",
            reply_markup=SkyMapKeyboards.back_to_main(),
        )
        await state.set_state(SkyMapStates.waiting_for_other_city)

    except Exception as e:
        logger.error(f"Ошибка обработки времени: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке времени. Попробуйте еще раз.",
            reply_markup=SkyMapKeyboards.back_to_main(),
        )


@router.callback_query(F.data == "skip_time")
async def skip_time_input(callback: CallbackQuery, state: FSMContext):
    """Пропуск ввода времени (используем 12:00)"""
    state_data = await state.get_data()
    birth_date = state_data["birth_date"]
    birth_datetime = birth_date.replace(hour=12, minute=0)

    await state.update_data(birth_datetime=birth_datetime)
    await callback.message.edit_text(
        "🏙️ <b>Место рождения</b>\n\n"
        "Введите город рождения:\n"
        "Например: <code>Москва</code> или <code>Санкт-Петербург</code>",
        reply_markup=SkyMapKeyboards.back_to_main(),
    )
    await state.set_state(SkyMapStates.waiting_for_other_city)


@router.message(SkyMapStates.waiting_for_other_city)
async def process_other_city(message: Message, state: FSMContext):
    """Обработка города для чужой карты"""
    city_name = message.text.strip()

    # Сначала проверяем валидность ввода
    is_valid, error_message = astro_service.validate_city_input(city_name)
    if not is_valid:
        await message.answer(
            f"❌ <b>Ошибка ввода:</b> {error_message}\n\n"
            "💡 <b>Примеры правильного ввода:</b>\n"
            "• Москва\n"
            "• Санкт-Петербург\n"
            "• Екатеринбург\n"
            "• Нью-Йорк\n\n"
            "Попробуйте еще раз:",
            reply_markup=SkyMapKeyboards.back_to_main(),
        )
        return

    # Получаем координаты города
    location = astro_service.get_location(city_name)
    if not location:
        await message.answer(
            "🌍 <b>Город не найден</b>\n\n"
            "Не удалось найти указанный город. Проверьте правильность написания.\n\n"
            "💡 <b>Попробуйте:</b>\n"
            "• Указать полное название (например, 'Ростов-на-Дону')\n"
            "• Добавить страну (например, 'Париж, Франция')\n"
            "• Проверить правильность написания\n\n"
            "Введите название города еще раз:",
            reply_markup=SkyMapKeyboards.back_to_main(),
        )
        return

    # Показываем статус обработки
    state_data = await state.get_data()
    other_name = state_data["other_name"]
    birth_datetime = state_data["birth_datetime"]

    processing_msg = await message.answer(
        f"🌌 <b>Создание карты для {other_name}...</b> ✨\n\n"
        "⏳ Рассчитываем позиции планет и звезд...\n"
        "🔭 Это может занять до 30 секунд"
    )

    try:
        # Рассчитываем натальную карту
        planets = await astro_service.calculate_natal_chart(birth_datetime, location)
        if not planets:
            await processing_msg.edit_text(
                "❌ Не удалось рассчитать натальную карту.\n"
                "Проверьте корректность данных.",
                reply_markup=SkyMapKeyboards.back_to_main(),
            )
            await state.clear()
            return

        # Создаем карту неба
        sky_image_bytes = await sky_service.create_birth_sky_map(
            birth_date=birth_datetime,
            location=location,
            planets=planets,
            owner_name=other_name,
        )

        if not sky_image_bytes:
            await processing_msg.edit_text(
                "❌ Не удалось создать карту звездного неба.\n" "Попробуйте позже.",
                reply_markup=SkyMapKeyboards.back_to_main(),
            )
            await state.clear()
            return

        # Формируем описание
        description = (
            f"🌌 <b>Звездное небо для {other_name}</b> ✨\n\n"
            f"📅 <b>Момент рождения:</b> {birth_datetime.strftime('%d.%m.%Y в %H:%M')}\n"
            f"📍 <b>Место:</b> {location.city}\n\n"
            f"🪐 В этот момент небесные тела выстроились в уникальную конфигурацию, "
            f"создавая персональный космический отпечаток.\n\n"
            f"✨ <i>Каждая карта звездного неба уникальна, как отпечаток пальца!</i>"
        )

        # Отправляем изображение
        image_file = BufferedInputFile(
            sky_image_bytes, filename=f"star_map_{other_name}.png"
        )
        await message.answer_photo(
            photo=image_file,
            caption=description,
            reply_markup=SkyMapKeyboards.sky_actions(),
        )

        # Удаляем сообщение о статусе
        await processing_msg.delete()
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка создания карты неба для другого человека: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка при создании карты звездного неба.\n"
            "Пожалуйста, попробуйте позже.",
            reply_markup=SkyMapKeyboards.back_to_main(),
        )
        await state.clear()


@router.callback_query(F.data == "create_another_sky")
async def create_another_sky(callback: CallbackQuery, state: FSMContext):
    """Создание еще одной карты неба"""
    await start_other_sky(callback, state)


@router.callback_query(F.data == "back_to_sky_menu")
async def back_to_sky_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню звездного неба"""
    await state.clear()
    text = (
        "🌌 <b>Звёздное небо</b> ✨\n\n"
        "В ту секунду, когда вы появились на свет, небо замерло — "
        "и выстроилось в уникальный узор. Планеты, звёзды, Луна — "
        "всё сложилось в космический отпечаток, который принадлежит только вам.\n\n"
        "✨ Готовы увидеть, как выглядело ваше небо?"
    )

    await callback.message.edit_text(text, reply_markup=SkyMapKeyboards.main_menu())
