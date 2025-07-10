import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db_manager
from keyboards import Keyboards
from services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = Router()

# Инициализируем сервис подписок
subscription_service = SubscriptionService()


@router.message(F.text.in_(["/subscription", "💎 Подписка"]))
async def subscription_menu_handler(message: Message, state: FSMContext):
    """Главное меню управления подпиской"""
    await state.clear()
    user_id = message.from_user.id
    
    # Получаем статус подписки пользователя
    subscription_status = subscription_service.get_user_subscription_status(user_id)
    is_premium = subscription_status.get("is_premium", False)
    days_remaining = subscription_status.get("days_remaining")
    
    if is_premium:
        if days_remaining is not None:
            title = f"💎 <b>Premium подписка активна</b>\n⏰ Осталось дней: {days_remaining}"
        else:
            title = "💎 <b>Premium подписка активна</b>\n♾️ Бессрочная подписка"
    else:
        title = "💎 <b>Управление подпиской</b>\n\n🆓 У вас бесплатная версия"
    
    await message.answer(
        title,
        reply_markup=Keyboards.subscription_menu(is_premium, days_remaining)
    )


@router.callback_query(F.data == "subscription_back")
async def subscription_back_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат в меню подписки"""
    user_id = callback.from_user.id
    
    # Получаем статус подписки пользователя
    subscription_status = subscription_service.get_user_subscription_status(user_id)
    is_premium = subscription_status.get("is_premium", False)
    days_remaining = subscription_status.get("days_remaining")
    
    if is_premium:
        if days_remaining is not None:
            title = f"💎 <b>Premium подписка активна</b>\n⏰ Осталось дней: {days_remaining}"
        else:
            title = "💎 <b>Premium подписка активна</b>\n♾️ Бессрочная подписка"
    else:
        title = "💎 <b>Управление подпиской</b>\n\n🆓 У вас бесплатная версия"
    
    await callback.message.edit_text(
        title,
        reply_markup=Keyboards.subscription_menu(is_premium, days_remaining)
    )
    await callback.answer()


@router.callback_query(F.data == "subscription_status")
async def subscription_status_handler(callback: CallbackQuery):
    """Показать подробный статус подписки"""
    user_id = callback.from_user.id
    
    subscription_status = subscription_service.get_user_subscription_status(user_id)
    is_premium = subscription_status.get("is_premium", False)
    
    if is_premium:
        days_remaining = subscription_status.get("days_remaining")
        status_text = subscription_service.get_subscription_status_text(user_id)
        
        text = f"""
📊 <b>Статус подписки</b>

{status_text}

🌟 <b>Доступные возможности:</b>
• 🪐 Полная натальная карта (все планеты)
• 🔮 Неограниченные вопросы
• 🌙 Детальные транзиты
• 📊 Неограниченные натальные карты
• 🏆 Приоритетная обработка
• 🎯 Персональные рекомендации

✨ Спасибо за то, что поддерживаете нас!
"""
    else:
        # Статистика для бесплатных пользователей
        user_charts = db_manager.get_user_charts(user_id)
        charts_count = len(user_charts)
        max_charts = subscription_service.FREE_USER_LIMITS["natal_charts"]
        
        text = f"""
📊 <b>Статус подписки</b>

🆓 <b>Бесплатная версия</b>

📈 <b>Использование:</b>
• 📊 Натальные карты: {charts_count}/{max_charts}
• 🪐 Планеты: только основные (Солнце, Луна, Асцендент)
• 🔮 Вопросы в день: 5

💡 <b>Хотите больше возможностей?</b>
Оформите Premium подписку и получите доступ ко всем функциям!
"""
    
    await callback.message.edit_text(
        text.strip(),
        reply_markup=Keyboards.subscription_menu(is_premium)
    )
    await callback.answer()


@router.callback_query(F.data == "subscription_benefits")
async def subscription_benefits_handler(callback: CallbackQuery):
    """Показать преимущества Premium подписки"""
    text = """
💎 <b>Преимущества Premium подписки</b>

🆓 <b>Бесплатная версия:</b>
• 1 натальная карта
• Только основные планеты (Солнце, Луна, Асцендент)
• 5 вопросов в день

💎 <b>Premium версия:</b>
• ♾️ Неограниченные натальные карты
• 🪐 Все планеты и аспекты (10+ планет)
• 🔮 Неограниченные вопросы Звёздному совету
• 🌙 Детальные транзиты и прогнозы
• 📈 Расширенная совместимость
• 🎯 Персональные рекомендации
• 🏆 Приоритетная обработка запросов
• 📱 Ранний доступ к новым функциям

💰 <b>Стоимость:</b> всего 499₽ в месяц


"""
    
    await callback.message.edit_text(
        text.strip(),
        reply_markup=Keyboards.subscription_upgrade_options()
    )
    await callback.answer()


@router.callback_query(F.data == "subscription_upgrade")
async def subscription_upgrade_handler(callback: CallbackQuery):
    """Показать варианты оформления подписки"""
    text = subscription_service.get_subscription_offer_text(callback.from_user.id)
    
    await callback.message.edit_text(
        text,
        reply_markup=Keyboards.subscription_upgrade_options()
    )
    await callback.answer()


@router.callback_query(F.data == "buy_monthly")
async def buy_monthly_handler(callback: CallbackQuery):
    """Обработка покупки месячной подписки"""
    # TODO: Интеграция с платёжной системой (ЮKassa, Stripe и т.д.)
    text = """
💳 <b>Оформление подписки</b>

🔄 <b>Система автоматических платежей в разработке...</b>

Интеграция с популярными платёжными системами (ЮKassa, Stripe, СберПей) будет добавлена в ближайших обновлениях для максимального удобства пользователей.

💎 После добавления платёжной системы подписка будет активироваться мгновенно!

🎁 <b>Специальное предложение:</b>
Первые 100 пользователей получают скидку 50%!
Стоимость: ~~499₽~~ → <b>249₽</b> в месяц
"""
    
    await callback.message.edit_text(
        text.strip(),
        reply_markup=Keyboards.subscription_upgrade_options()
    )
    await callback.answer()



@router.callback_query(F.data == "subscription_faq")
async def subscription_faq_handler(callback: CallbackQuery):
    """Часто задаваемые вопросы о подписке"""
    text = """
❓ <b>Часто задаваемые вопросы</b>

<b>Q: Как работает Premium подписка?</b>
A: После оплаты вы получаете доступ ко всем функциям на 30 дней.

<b>Q: Можно ли отменить подписку?</b>
A: Да, вы можете отменить подписку в любой момент.

<b>Q: Что происходит после отмены?</b>
A: Вы продолжаете пользоваться Premium до конца оплаченного периода.

<b>Q: Когда появятся автоматические платежи?</b>
A: Интеграция с популярными платёжными системами планируется в ближайших обновлениях.

<b>Q: Безопасны ли будут платежи?</b>
A: Да, будут использоваться только проверенные платёжные системы с шифрованием.

<b>Q: Есть ли скидки?</b>
A: Первые 100 пользователей получают скидку 50%!
"""
    
    await callback.message.edit_text(
        text.strip(),
        reply_markup=Keyboards.subscription_upgrade_options()
    )
    await callback.answer()


@router.callback_query(F.data == "subscription_renew")
async def subscription_renew_handler(callback: CallbackQuery):
    """Продление подписки"""
    text = """
🔄 <b>Продление подписки</b>

💎 Ваша Premium подписка будет автоматически продлена при приближении к окончанию.

💳 <b>Способы продления:</b>
• Автоматическое продление (рекомендуется)
• Ручное продление через поддержку

⚙️ <b>Настройки автопродления:</b>
Функция автоматического продления будет добавлена вместе с интеграцией платёжных систем.

🔄 <b>Планируемые возможности:</b>
• Настройка автопродления
• Уведомления об истечении подписки
• Гибкие тарифные планы
"""
    
    await callback.message.edit_text(
        text.strip(),
        reply_markup=Keyboards.subscription_menu(is_premium=True)
    )
    await callback.answer()


@router.callback_query(F.data == "subscription_cancel")
async def subscription_cancel_handler(callback: CallbackQuery):
    """Запрос на отмену подписки"""
    text = """
😔 <b>Отмена подписки</b>

Вы уверены, что хотите отменить Premium подписку?

❗ <b>Обратите внимание:</b>
• Подписка будет отменена с конца текущего периода
• Вы сохраните доступ к Premium до окончания оплаченного времени
• Ваши данные останутся сохранёнными

💔 <b>Расскажите, почему вы уходите?</b>
Это поможет нам стать лучше.

🎁 <b>Хотите скидку?</b>
Свяжитесь с поддержкой - возможно, мы найдём компромисс!
"""
    
    await callback.message.edit_text(
        text.strip(),
        reply_markup=Keyboards.subscription_confirm_cancel()
    )
    await callback.answer()


@router.callback_query(F.data == "subscription_cancel_confirm")
async def subscription_cancel_confirm_handler(callback: CallbackQuery):
    """Подтверждение отмены подписки"""
    user_id = callback.from_user.id
    
    # Отменяем подписку
    success = subscription_service.cancel_subscription(user_id)
    
    if success:
        text = """
✅ <b>Подписка отменена</b>

😔 Нам жаль, что вы уходите!

ℹ️ <b>Что дальше:</b>
• Premium остаётся активным до конца оплаченного периода
• После этого аккаунт переключится на бесплатную версию
• Ваши данные сохранятся

🎯 <b>Мы стараемся стать лучше!</b>
Если передумаете - Premium всегда можно вернуть.

💌 <b>Ваше мнение важно!</b>
Мы постоянно работаем над улучшением сервиса и учитываем пожелания пользователей.

🌟 Спасибо, что были с нами! Двери всегда открыты.
"""
        
        # Обновляем меню на бесплатную версию
        await callback.message.edit_text(
            text.strip(),
            reply_markup=Keyboards.subscription_menu(is_premium=False)
        )
        logger.info(f"Пользователь {user_id} отменил подписку")
    else:
        text = """
❌ <b>Ошибка отмены подписки</b>

Произошла ошибка при отмене подписки.

🔧 <b>Что делать:</b>
• Попробуйте позже
• Перезапустите бота командой /start

😔 Приносим извинения за неудобства!
"""
        await callback.message.edit_text(
            text.strip(),
            reply_markup=Keyboards.subscription_menu(is_premium=True)
        )
        logger.error(f"Ошибка отмены подписки для пользователя {user_id}")
    
    await callback.answer() 