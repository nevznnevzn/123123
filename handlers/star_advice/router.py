import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database_async import async_db_manager
from services.antispam_service import AntiSpamService
from services.astro_calculations import AstroService
from services.star_advice_service import StarAdviceService
from services.subscription_service import SubscriptionService

from .keyboards import StarAdviceKeyboards
from .states import StarAdviceStates

logger = logging.getLogger(__name__)

router = Router()

# Инициализируем сервисы
astro_service = AstroService()
star_advice_service = StarAdviceService()
antispam_service = AntiSpamService()
subscription_service = SubscriptionService()


@router.message(F.text == "🌟 Звёздный совет")
async def star_advice_start(message: Message, state: FSMContext):
    """Главное меню Звёздного совета"""
    await state.clear()
    user_id = message.from_user.id

    # Проверяем заполнен ли профиль
    user_profile = await async_db_manager.get_user_profile(user_id)
    if not user_profile or not user_profile.is_profile_complete:
        await message.answer(
            "🌟 <b>Звёздный совет</b> ✨\n\n"
            "Для получения персональных астрологических советов необходимо заполнить профиль.",
            reply_markup=StarAdviceKeyboards.back_to_categories(),
        )
        return

    # Показываем статистику лимитов
    is_premium = await subscription_service.is_user_premium(user_id)
    stats_text = antispam_service.get_stats_text(user_id, is_premium)

    text = (
        "🌟 <b>Звёздный совет</b> ✨\n\n"
        "Задайте свой вопрос, и я предоставлю совет, основываясь на "
        "актуальных транзитах и вашей натальной карте.\n\n"
        f"{stats_text}\n"
        "💫 Выберите категорию вашего вопроса:"
    )

    await message.answer(text, reply_markup=StarAdviceKeyboards.categories_menu())


@router.callback_query(F.data.startswith("star_advice_"))
async def handle_category_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    category = callback.data.split("_")[2]  # star_advice_career -> career
    user_id = callback.from_user.id

    if category == "back":
        await star_advice_start_callback(callback, state)
        return

    # Проверяем лимиты перед началом
    is_premium = await subscription_service.is_user_premium(user_id)
    limits_check = antispam_service.check_limits(user_id, is_premium)

    if not limits_check["allowed"]:
        await handle_limits_exceeded(callback, limits_check)
        return

    # Сохраняем выбранную категорию
    await state.update_data(category=category)

    # Получаем описание категории
    category_descriptions = {
        "career": "💼 работы и карьеры",
        "love": "❤️ отношений и любви",
        "finances": "💰 финансов и ресурсов",
        "family": "🏠 семьи и дома",
        "growth": "🌱 личностного роста",
        "other": "✍️ общих жизненных вопросов",
    }

    category_desc = category_descriptions.get(category, "общих вопросов")

    text = (
        f"🌟 <b>Звёздный совет по вопросам {category_desc}</b> ✨\n\n"
        "📝 Опишите вашу ситуацию или задайте вопрос.\n\n"
        "💡 <b>Советы для хорошего ответа:</b>\n"
        "• Опишите конкретную ситуацию\n"
        "• Укажите что вас беспокоит\n"
        "• Задайте конкретный вопрос\n\n"
        "⚠️ <b>Ограничения:</b> 10-500 символов"
    )

    await callback.message.edit_text(
        text, reply_markup=StarAdviceKeyboards.back_to_categories()
    )
    await state.set_state(StarAdviceStates.waiting_for_question)


@router.message(StarAdviceStates.waiting_for_question)
async def process_question(message: Message, state: FSMContext):
    """Обработка вопроса пользователя"""
    user_id = message.from_user.id
    question = message.text.strip()

    # Получаем данные состояния
    state_data = await state.get_data()
    category = state_data.get("category", "other")

    # Валидация вопроса
    validation_result = await star_advice_service.validate_question(question)
    if not validation_result["is_valid"]:
        await message.answer(
            f"❌ <b>Вопрос не принят</b>\n\n"
            f"{validation_result['reason']}\n\n"
            "Попробуйте переформулировать ваш вопрос.",
            reply_markup=StarAdviceKeyboards.back_to_categories(),
        )
        return

    # Финальная проверка лимитов перед генерацией
    is_premium = await subscription_service.is_user_premium(user_id)
    limits_check = antispam_service.check_limits(user_id, is_premium)

    if not limits_check["allowed"]:
        await handle_limits_exceeded_message(message, limits_check)
        await state.clear()
        return

    # Записываем использование лимита
    antispam_service.record_question(user_id)

    # Отображаем статус обработки
    processing_msg = await message.answer(
        "⏳ <b>Звёзды размышляют...</b> 🌙\n\n✨ Анализирую вашу ситуацию... Это может занять до 30 секунд."
    )

    try:
        # Получаем данные пользователя
        user_profile = await async_db_manager.get_user_profile(user_id)
        location = astro_service.get_location(user_profile.birth_city)

        if not location:
            await processing_msg.edit_text(
                "❌ Не удалось получить данные о вашем местоположении. "
                "Проверьте корректность города в профиле.",
                reply_markup=StarAdviceKeyboards.back_to_categories(),
            )
            await state.clear()
            return

        # Рассчитываем натальную карту асинхронно
        planets = await astro_service.calculate_natal_chart(user_profile.birth_date, location)

        if not planets:
            await processing_msg.edit_text(
                "❌ Не удалось рассчитать натальную карту. "
                "Проверьте корректность данных в профиле.",
                reply_markup=StarAdviceKeyboards.back_to_categories(),
            )
            await state.clear()
            return

        # Фильтруем планеты в зависимости от подписки
        filtered_planets = await subscription_service.filter_planets_for_user(
            planets, user_id
        )

        # Генерируем совет
        advice = await star_advice_service.generate_advice(
            question=question,
            category=category,
            user_planets=filtered_planets,
            birth_dt=user_profile.birth_date,
            location=location,
            user_name=user_profile.name,
        )

        # Добавляем информацию о лимитах в конец
        remaining_questions = limits_check["questions_left"]
        if remaining_questions > 0 and not is_premium:
            advice += f"\n\n📊 Осталось вопросов сегодня: <b>{remaining_questions}</b>"
        elif remaining_questions == 0 and not is_premium:
            advice += "\n\n💎 Лимит исчерпан. Получите Premium для неограниченных консультаций!"

        await processing_msg.edit_text(
            advice, reply_markup=StarAdviceKeyboards.back_to_categories()
        )

    except Exception as e:
        logger.error(f"Ошибка генерации совета: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка при генерации совета. Пожалуйста, попробуйте позже.",
            reply_markup=StarAdviceKeyboards.back_to_categories(),
        )

    await state.clear()


async def handle_limits_exceeded(callback: CallbackQuery, limits_check: dict):
    """Обработка превышения лимитов (callback)"""
    reason = limits_check["reason"]

    if reason == "daily_limit":
        text = (
            "📊 <b>Дневной лимит исчерпан</b> ⏰\n\n"
            "Вы задали максимальное количество вопросов на сегодня.\n\n"
            "💎 Получите Premium для неограниченных консультаций!"
        )
        keyboard = StarAdviceKeyboards.limit_reached_keyboard()

    elif reason == "cooldown":
        wait_time = antispam_service.format_wait_time(limits_check["wait_time"])
        text = (
            f"⏰ <b>Кулдаун активен</b>\n\n"
            f"Следующий вопрос можно задать через: <b>{wait_time}</b>\n\n"
            f"Осталось вопросов сегодня: <b>{limits_check['questions_left']}</b>"
        )
        keyboard = StarAdviceKeyboards.cooldown_keyboard()

    else:
        text = "❌ Произошла ошибка проверки лимитов."
        keyboard = StarAdviceKeyboards.back_to_categories()

    await callback.message.edit_text(text, reply_markup=keyboard)


async def handle_limits_exceeded_message(message: Message, limits_check: dict):
    """Обработка превышения лимитов (message)"""
    reason = limits_check["reason"]

    if reason == "daily_limit":
        text = (
            "📊 <b>Дневной лимит исчерпан</b> ⏰\n\n"
            "Вы задали максимальное количество вопросов на сегодня.\n\n"
            "💎 Получите Premium для неограниченных консультаций!"
        )
        keyboard = StarAdviceKeyboards.limit_reached_keyboard()

    elif reason == "cooldown":
        wait_time = antispam_service.format_wait_time(limits_check["wait_time"])
        text = (
            f"⏰ <b>Кулдаун активен</b>\n\n"
            f"Следующий вопрос можно задать через: <b>{wait_time}</b>\n\n"
            f"Осталось вопросов сегодня: <b>{limits_check['questions_left']}</b>"
        )
        keyboard = StarAdviceKeyboards.cooldown_keyboard()

    else:
        text = "❌ Произошла ошибка проверки лимитов."
        keyboard = StarAdviceKeyboards.back_to_categories()

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "star_advice_back")
async def star_advice_start_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат к главному меню Звёздного совета"""
    await state.clear()
    user_id = callback.from_user.id

    # Показываем статистику лимитов
    is_premium = False  # TODO: Интеграция с системой подписки
    stats_text = antispam_service.get_stats_text(user_id, is_premium)

    text = (
        "🌟 <b>Звёздный совет</b> ✨\n\n"
        "Задайте свой вопрос, и я предоставлю совет, основываясь на "
        "актуальных транзитах и вашей натальной карте.\n\n"
        f"{stats_text}\n"
        "💫 Выберите категорию вашего вопроса:"
    )

    await callback.message.edit_text(
        text, reply_markup=StarAdviceKeyboards.categories_menu()
    )


# Обработчики для кнопок лимитов
@router.callback_query(F.data == "get_premium")
async def get_premium_info(callback: CallbackQuery):
    """Информация о премиум подписке"""
    text = (
        "💎 <b>Premium подписка</b> ✨\n\n"
        "🌟 <b>Преимущества Premium:</b>\n"
        "• Неограниченные вопросы Звёздному совету\n"
        "• Минимальный кулдаун (1 минута)\n"
        "• Приоритетная обработка запросов\n"
        "• Расширенные астрологические функции\n\n"
        "💰 <b>Стоимость:</b> 499₽ в месяц\n\n"
        "🚀 Скоро будет доступна покупка!"
    )

    await callback.message.edit_text(
        text, reply_markup=StarAdviceKeyboards.back_to_categories()
    )
