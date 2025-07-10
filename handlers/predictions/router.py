import logging
import time
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db_manager
from keyboards import Keyboards
from services.ai_predictions import AIPredictionService

logger = logging.getLogger(__name__)

router = Router()
ai_service = AIPredictionService()


def format_charts_word(count: int) -> str:
    """Правильное склонение слова 'карта' в зависимости от количества"""
    last_digit = count % 10
    last_two_digits = count % 100
    if 11 <= last_two_digits <= 14:
        return "карт"
    if last_digit == 1:
        return "карта"
    if 2 <= last_digit <= 4:
        return "карты"
    return "карт"


@router.message(F.text == "🔮 Прогнозы")
async def predictions_menu(message: Message):
    """Меню прогнозов"""
    user_id = message.from_user.id
    charts = db_manager.get_user_charts(user_id)

    if not charts:
        await message.answer(
            "🔮 <b>Астрологические прогнозы</b> ✨\n\n"
            "📊 У вас нет натальных карт, для которых можно было бы составить прогноз.\n"
            "🌟 Пожалуйста, сначала создайте карту.",
            reply_markup=Keyboards.prediction_charts_list([]),
        )
        return

    text = (
        "🔮 <b>Астрологические прогнозы</b> ✨\n\n"
        f"📊 У вас {len(charts)} сохраненных {format_charts_word(len(charts))}.\n"
        "⭐ Выберите одну из них, чтобы составить новый прогноз или просмотреть существующие."
    )

    await message.answer(text, reply_markup=Keyboards.prediction_charts_list(charts))


@router.callback_query(F.data.startswith("predict_chart_"))
async def select_chart_for_prediction(callback: CallbackQuery):
    """Выбор карты для создания прогноза"""
    chart_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    chart = db_manager.get_chart_by_id(chart_id, user_id)

    if not chart:
        await callback.answer("Карта не найдена!", show_alert=True)
        return

    owner_name = chart.chart_owner_name or "Ваша карта"
    text = f"🌟 <b>Выбрана карта:</b> {owner_name} ({chart.city}) ✨\n\n🔮 Выберите период для прогноза:"

    await callback.message.edit_text(
        text, reply_markup=Keyboards.prediction_types(chart_id)
    )


@router.callback_query(F.data.startswith("prediction_"))
async def generate_prediction(callback: CallbackQuery):
    """Генерация прогноза"""
    parts = callback.data.split("_")
    period = parts[1]
    chart_id = int(parts[2])

    user_id = callback.from_user.id
    chart = db_manager.get_chart_by_id(chart_id, user_id)
    if not chart:
        await callback.answer("Карта не найдена!", show_alert=True)
        return

    # Проверяем, есть ли уже действующий прогноз этого типа
    existing_prediction = db_manager.find_valid_prediction(user_id, chart_id, period)
    if existing_prediction:
        # Показываем существующий прогноз с дополнительной информацией
        period_display = ai_service._get_period_display(
            period, existing_prediction.valid_from, existing_prediction.valid_until
        )
        created_date = existing_prediction.created_at.strftime("%d.%m.%Y в %H:%M")

        # Добавляем информацию о том, что это сохранённый прогноз
        info_header = f"💾 <b>Сохранённый прогноз</b>\n📅 {period_display}\n🕐 Создан: {created_date}\n\n"
        full_content = info_header + existing_prediction.content

        await callback.message.edit_text(
            full_content, reply_markup=Keyboards.back_to_main_menu()
        )
        return

    # Показываем сообщение о генерации с прогрессом
    progress_msg = await callback.message.edit_text(
        "⏳ <b>Звезды шепчут...</b> 🌙\n\n✨ Генерирую прогноз... Ожидайте до 20 секунд."
    )
    
    # Через 10 секунд показываем дополнительное сообщение
    import asyncio
    async def show_progress():
        await asyncio.sleep(10)
        try:
            await progress_msg.edit_text(
                "⏳ <b>Звезды все еще шепчут...</b> 🌙\n\n✨ Почти готово... Еще немного терпения!"
            )
        except:
            pass  # Игнорируем ошибки редактирования
    
    # Запускаем прогресс в фоне
    asyncio.create_task(show_progress())

    # Получаем период действия прогноза из AI сервиса
    valid_from, valid_until = ai_service.get_prediction_period(period)

    # Получаем все нужные данные для генерации
    planets = chart.get_planets_data()
    owner_name = chart.chart_owner_name or "Ваша карта"
    birth_dt = chart.birth_date
    location = None  # Временно отключаем геолокацию

    # Засекаем время генерации
    start_time = time.time()

    # Генерируем прогноз через AI с обработкой ошибок
    try:
        prediction_text = await ai_service.generate_prediction(
            user_planets=planets,
            prediction_type=period,
            owner_name=owner_name,
            birth_dt=birth_dt,
            location=location,
        )
    except Exception as e:
        logger.error(f"Критическая ошибка генерации прогноза: {e}")
        await callback.message.edit_text(
            "❌ <b>Сервис прогнозов временно недоступен</b>\n\n"
            "🔧 Попробуйте позже или обратитесь к администратору.",
            reply_markup=Keyboards.back_to_main_menu(),
        )
        return

    generation_time = time.time() - start_time

    if "❌" in prediction_text or "ошибка" in prediction_text.lower():
        await callback.message.edit_text(
            f"❌ Не удалось сгенерировать прогноз для <b>{owner_name}</b>. Попробуйте позже.",
            reply_markup=Keyboards.back_to_main_menu(),
        )
    else:
        # Сохраняем успешный прогноз в базу данных
        try:
            db_manager.create_prediction(
                telegram_id=user_id,
                chart_id=chart_id,
                prediction_type=period,
                valid_from=valid_from,
                valid_until=valid_until,
                content=prediction_text,
                generation_time=generation_time,
            )

            await callback.message.edit_text(
                prediction_text, reply_markup=Keyboards.back_to_main_menu()
            )

            # Показываем подсказку о том, что прогноз сохранен
            period_display = ai_service._get_period_display(
                period, valid_from, valid_until
            )
            await callback.answer(
                f"✅ Прогноз сохранен: {period_display}", show_alert=False
            )

        except Exception as e:
            # Если не удалось сохранить, все равно показываем прогноз
            await callback.message.edit_text(
                prediction_text, reply_markup=Keyboards.back_to_main_menu()
            )
            await callback.answer("⚠️ Прогноз создан, но не сохранен", show_alert=False)


@router.callback_query(F.data == "back_to_pred_charts")
async def back_to_prediction_charts(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку карт для прогноза"""
    await callback.answer()
    await predictions_menu(callback.message)


@router.callback_query(F.data.startswith("view_specific_prediction"))
async def view_specific_prediction(callback: CallbackQuery):
    """Просмотр конкретного прогноза"""
    prediction_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    # Получаем прогноз и проверяем, что он принадлежит пользователю
    predictions = db_manager.get_user_predictions(user_id, active_only=False)
    prediction = next((p for p in predictions if p.id == prediction_id), None)

    if not prediction:
        await callback.answer("Прогноз не найден!", show_alert=True)
        return

    # Проверяем, что прогноз еще действителен
    if not prediction.is_valid():
        await callback.answer("Этот прогноз больше не действителен", show_alert=True)
        return

    # Показываем прогноз
    await callback.message.edit_text(
        prediction.content, reply_markup=Keyboards.back_to_main_menu()
    )


@router.callback_query(F.data.startswith("create_new_prediction_"))
async def create_new_prediction_menu(callback: CallbackQuery):
    """Меню создания нового прогноза (возврат из списка активных)"""
    chart_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    chart = db_manager.get_chart_by_id(chart_id, user_id)

    if not chart:
        await callback.answer("Карта не найдена!", show_alert=True)
        return

    owner_name = chart.chart_owner_name or "Ваша карта"
    text = f"🌟 <b>Выбрана карта:</b> {owner_name} ({chart.city}) ✨\n\n🔮 Выберите период для прогноза:"

    await callback.message.edit_text(
        text, reply_markup=Keyboards.prediction_types(chart_id)
    )
