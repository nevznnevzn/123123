import asyncio
import logging
import platform
import sys
from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import DatabaseManager
from database_async import async_db_manager

from . import keyboards
from .states import AdminStates

logger = logging.getLogger(__name__)


def create_admin_router(db_manager=None) -> Router:
    """Создает и настраивает роутер для админ-панели."""
    from database_async import async_db_manager
    if db_manager is None:
        db_manager = async_db_manager
    router = Router()

    @router.message(Command("admin"))
    async def admin_start(message: Message):
        """Начало работы с админ-панелью."""
        await message.answer(
            "🔧 **Админ-панель Solar Balance**\n\nВыберите раздел для управления:",
            reply_markup=keyboards.main_admin_keyboard(),
        )

    @router.callback_query(F.data == "admin_panel")
    async def admin_panel_callback(callback: CallbackQuery):
        """Возврат в главное меню админ-панели."""
        await callback.message.edit_text(
            "🔧 **Админ-панель Solar Balance**\n\nВыберите раздел для управления:",
            reply_markup=keyboards.main_admin_keyboard(),
        )
        await callback.answer()

    # === УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ===

    @router.callback_query(F.data == "admin_users")
    async def admin_users_menu(callback: CallbackQuery):
        """Меню управления пользователями."""
        await callback.message.edit_text(
            "👥 **Управление пользователями**\n\nВыберите действие:",
            reply_markup=keyboards.users_management_keyboard(),
        )
        await callback.answer()

    @router.callback_query(F.data == "admin_user_search")
    async def admin_user_search_start(callback: CallbackQuery, state: FSMContext):
        """Начало поиска пользователя."""
        await state.set_state(AdminStates.user_search)
        await callback.message.edit_text(
            "🔍 **Поиск пользователя**\n\nВведите Telegram ID пользователя:",
            reply_markup=keyboards.back_to_main_admin_keyboard(),
        )
        await callback.answer()

    @router.message(AdminStates.user_search)
    async def admin_search_user(
        message: Message, state: FSMContext
    ):
        """Поиск пользователя по ID."""
        if not message.text.isdigit():
            await message.answer("❌ Некорректный ID. Введите числовой Telegram ID.")
            return

        user_id = int(message.text)
        user = await async_db_manager.get_user_profile(user_id)

        if user:
            sub = user.subscription
            sub_status = "Активна" if user.is_premium else "Отсутствует"
            if sub and sub.end_date:
                sub_status += f" до {sub.end_date.strftime('%d.%m.%Y')}"

            profile_text = (
                f"👤 **Профиль пользователя**\n\n"
                f"**ID:** `{user.telegram_id}`\n"
                f"**Имя:** {user.name}\n"
                f"**Регистрация:** {user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"**Premium:** {sub_status}\n"
                f"**Профиль завершен:** {'✅' if user.is_profile_complete else '❌'}"
            )
            await message.answer(
                profile_text,
                reply_markup=keyboards.user_profile_keyboard(user_id, user.is_premium),
            )
        else:
            await message.answer("❌ Пользователь не найден.")

        await state.clear()

    @router.callback_query(F.data.startswith("admin_users_list"))
    async def admin_users_list(callback: CallbackQuery):
        """Список всех пользователей."""
        await show_users_list(callback, 1, "all")

    @router.callback_query(F.data.startswith("admin_active_users"))
    async def admin_active_users(callback: CallbackQuery):
        """Список активных пользователей."""
        await show_users_list(callback, 1, "active")

    @router.callback_query(F.data.startswith("admin_premium_users"))
    async def admin_premium_users(callback: CallbackQuery):
        """Список премиум пользователей."""
        await show_users_list(callback, 1, "premium")

    @router.callback_query(F.data.startswith("users_page_"))
    async def admin_users_pagination(callback: CallbackQuery):
        """Пагинация списка пользователей."""
        parts = callback.data.split("_")
        list_type = parts[2]
        page = int(parts[3])
        await show_users_list(callback, page, list_type)

    async def show_users_list(
        callback: CallbackQuery,
        page: int,
        list_type: str,
    ):
        """Показать список пользователей с пагинацией."""
        users, total_pages = await async_db_manager.get_users_paginated(page, 10, list_type)

        if not users:
            await callback.message.edit_text(
                "👥 Пользователи не найдены.",
                reply_markup=keyboards.back_to_main_admin_keyboard(),
            )
            await callback.answer()
            return

        type_names = {
            "all": "Все пользователи",
            "active": "Активные пользователи",
            "premium": "Premium пользователи",
        }
        title = type_names.get(list_type, "Пользователи")

        text = f"👥 **{title}** (стр. {page}/{total_pages})\n\n"

        for user in users:
            premium_status = "💎" if user.is_premium else "🆓"
            text += f"{premium_status} `{user.telegram_id}` - {user.name}\n"
            text += f"   📅 {user.created_at.strftime('%d.%m.%Y')}\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=keyboards.user_list_navigation_keyboard(
                page, total_pages, list_type
            ),
        )
        await callback.answer()

    # === УПРАВЛЕНИЕ ПОДПИСКАМИ ===

    @router.callback_query(F.data == "admin_subscriptions")
    async def admin_subscriptions_menu(callback: CallbackQuery):
        """Меню управления подписками."""
        await callback.message.edit_text(
            "💎 **Управление подписками**\n\nВыберите действие:",
            reply_markup=keyboards.subscriptions_management_keyboard(),
        )
        await callback.answer()

    @router.callback_query(F.data == "admin_grant_premium")
    async def admin_grant_premium_start(callback: CallbackQuery, state: FSMContext):
        """Начало выдачи Premium."""
        await state.set_state(AdminStates.premium_user_search)
        await callback.message.edit_text(
            "💎 **Выдача Premium подписки**\n\nВведите Telegram ID пользователя:",
            reply_markup=keyboards.back_to_main_admin_keyboard(),
        )
        await callback.answer()

    @router.message(AdminStates.premium_user_search)
    async def admin_grant_premium_user_found(
        message: Message, state: FSMContext
    ):
        """Пользователь найден, выбор срока Premium."""
        if not message.text.isdigit():
            await message.answer("❌ Некорректный ID. Введите числовой Telegram ID.")
            return

        user_id = int(message.text)
        user = await async_db_manager.get_user_profile(user_id)

        if user:
            await state.update_data(target_user_id=user_id)
            await message.answer(
                f"👤 **Пользователь:** {user.name} (`{user.telegram_id}`)\n\n💎 Выберите срок Premium подписки:",
                reply_markup=keyboards.premium_duration_keyboard(user_id),
            )
        else:
            await message.answer("❌ Пользователь не найден.")

        await state.clear()

    @router.callback_query(F.data.startswith("premium_"))
    async def admin_premium_duration_selected(
        callback: CallbackQuery
    ):
        """Выдача Premium на выбранный срок."""
        parts = callback.data.split("_")
        duration = parts[1]
        user_id = int(parts[2])

        days_map = {"7": 7, "30": 30, "90": 90, "365": 365, "unlimited": None}
        days = days_map.get(duration)

        if days is None:  # Бессрочная подписка
            await async_db_manager.create_premium_subscription(user_id, duration_days=99999)
            duration_text = "бессрочно"
        else:
            await async_db_manager.create_premium_subscription(user_id, duration_days=days)
            duration_text = f"{days} дней"

        await callback.answer(f"✅ Premium выдан на {duration_text}!", show_alert=True)
        await callback.message.edit_text(
            f"✅ **Premium подписка выдана**\n\n👤 Пользователь: `{user_id}`\n⏰ Срок: {duration_text}",
            reply_markup=keyboards.back_to_main_admin_keyboard(),
        )

    @router.callback_query(F.data == "admin_revoke_premium")
    async def admin_revoke_premium_start(callback: CallbackQuery, state: FSMContext):
        """Начало отзыва Premium."""
        await state.set_state(AdminStates.revoke_user_search)
        await callback.message.edit_text(
            "❌ **Отзыв Premium подписки**\n\nВведите Telegram ID пользователя:",
            reply_markup=keyboards.back_to_main_admin_keyboard(),
        )
        await callback.answer()

    @router.message(AdminStates.revoke_user_search)
    async def admin_revoke_premium_execute(
        message: Message, state: FSMContext
    ):
        """Отзыв Premium подписки."""
        if not message.text.isdigit():
            await message.answer("❌ Некорректный ID. Введите числовой Telegram ID.")
            return

        user_id = int(message.text)
        success = await async_db_manager.revoke_premium_subscription(user_id)

        if success:
            await message.answer("✅ Premium подписка отозвана.")
        else:
            await message.answer(
                "❌ Пользователь не найден или у него нет активной подписки."
            )

        await state.clear()

    @router.callback_query(F.data == "admin_sub_stats")
    async def admin_subscription_stats(
        callback: CallbackQuery
    ):
        """Статистика подписок."""
        stats = await async_db_manager.get_detailed_statistics()

        text = (
            f"�� **Статистика подписок**\n\n"
            f"💎 **Активных Premium:** {stats['active_premium']}\n"
            f"👥 **Всего пользователей:** {stats['total_users']}\n"
            f"📊 **Завершенных профилей:** {stats['complete_profiles']}\n"
            f"📈 **Всего карт:** {stats['total_charts']}\n"
            f"🔮 **Всего прогнозов:** {stats['total_predictions']}"
        )

        await callback.message.edit_text(
            text, reply_markup=keyboards.back_to_main_admin_keyboard()
        )
        await callback.answer()

    @router.callback_query(F.data == "admin_bulk_extend")
    async def admin_bulk_extend_menu(callback: CallbackQuery):
        """Меню массового управления Premium."""
        await callback.message.edit_text(
            "🔄 **Массовое управление Premium**\n\nВыберите действие:",
            reply_markup=keyboards.bulk_premium_keyboard(),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("bulk_"))
    async def admin_bulk_premium_actions(
        callback: CallbackQuery
    ):
        """Массовые действия с Premium."""
        action = callback.data.split("_", 1)[1]

        if action == "premium_30_active":
            # 30 дней всем активным пользователям последние 7 дней
            week_ago = datetime.utcnow() - timedelta(days=7)
            users, _ = await async_db_manager.get_users_paginated(1, 1000, "active")
            count = 0
            for user in users:
                await async_db_manager.create_premium_subscription(
                    user.telegram_id, duration_days=30
                )
                count += 1

            await callback.answer(
                f"✅ Premium выдан {count} пользователям!", show_alert=True
            )

        elif action == "premium_7_new":
            # 7 дней новым пользователям за сегодня
            today_start = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            users, _ = await async_db_manager.get_users_paginated(1, 1000, "all")
            count = 0
            for user in users:
                if user.created_at >= today_start:
                    await async_db_manager.create_premium_subscription(
                        user.telegram_id, duration_days=7
                    )
                    count += 1

            await callback.answer(
                f"✅ Premium выдан {count} новым пользователям!", show_alert=True
            )

        elif action == "extend_expiring":
            # Продлить истекающие подписки
            users = await async_db_manager.get_expiring_subscriptions(7)
            count = await async_db_manager.bulk_extend_premium([u.telegram_id for u in users], 30)

            await callback.answer(f"✅ Продлено {count} подписок!", show_alert=True)

        await callback.message.edit_text(
            "✅ **Массовая операция выполнена**",
            reply_markup=keyboards.back_to_main_admin_keyboard(),
        )

    @router.callback_query(F.data == "admin_cleanup_expired")
    async def admin_cleanup_expired(
        callback: CallbackQuery
    ):
        """Очистка истекших подписок."""
        count = await async_db_manager.check_and_expire_subscriptions()
        await callback.answer(
            f"✅ Обновлено {count} истекших подписок!", show_alert=True
        )
        await callback.message.edit_text(
            f"✅ **Очистка завершена**\n\nОбновлено {count} истекших подписок.",
            reply_markup=keyboards.back_to_main_admin_keyboard(),
        )

    # === СИСТЕМНОЕ УПРАВЛЕНИЕ ===

    @router.callback_query(F.data == "admin_system")
    async def admin_system_menu(callback: CallbackQuery):
        """Меню системного управления."""
        await callback.message.edit_text(
            "⚙️ **Системное управление**\n\nВыберите действие:",
            reply_markup=keyboards.system_management_keyboard(),
        )
        await callback.answer()

    @router.callback_query(F.data == "admin_detailed_stats")
    async def admin_detailed_stats(
        callback: CallbackQuery
    ):
        """Подробная статистика."""
        stats = await async_db_manager.get_detailed_statistics()

        text = (
            f"📈 **Подробная статистика**\n\n"
            f"👥 **Пользователи:**\n"
            f"  • Всего: {stats['total_users']}\n"
            f"  • Завершенных профилей: {stats['complete_profiles']}\n\n"
            f"💎 **Подписки:**\n"
            f"  • Активных Premium: {stats['active_premium']}\n\n"
            f"📊 **Контент:**\n"
            f"  • Натальных карт: {stats['total_charts']}\n"
            f"  • Прогнозов: {stats['total_predictions']}"
        )

        await callback.message.edit_text(
            text, reply_markup=keyboards.back_to_main_admin_keyboard()
        )
        await callback.answer()

    @router.callback_query(F.data == "admin_tech_info")
    async def admin_tech_info(callback: CallbackQuery):
        """Техническая информация о системе."""
        text = (
            f"🔧 **Техническая информация**\n\n"
            f"**Python:** {sys.version.split()[0]}\n"
            f"**Платформа:** {platform.system()} {platform.release()}\n"
            f"**Время сервера:** {datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')} UTC\n"
            f"**Версия бота:** Solar Balance v2.0"
        )

        await callback.message.edit_text(
            text, reply_markup=keyboards.back_to_main_admin_keyboard()
        )
        await callback.answer()

    @router.callback_query(F.data == "admin_cleanup_db")
    async def admin_cleanup_db(callback: CallbackQuery, db_manager: DatabaseManager):
        """Очистка базы данных."""
        result = await async_db_manager.cleanup_database()

        text = (
            f"�� **Очистка базы данных завершена**\n\n"
            f"✅ Удалено устаревших прогнозов: {result['expired_predictions_removed']}\n"
            f"✅ Обновлено истекших подписок: {result['subscriptions_expired']}"
        )

        await callback.message.edit_text(
            text, reply_markup=keyboards.back_to_main_admin_keyboard()
        )
        await callback.answer()

    # === ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ===

    @router.callback_query(F.data.startswith("grant_premium_"))
    async def admin_grant_premium_legacy(
        callback: CallbackQuery
    ):
        """Выдача Premium-статуса пользователю (legacy для совместимости)."""
        user_id = int(callback.data.split("_")[-1])
        await async_db_manager.create_premium_subscription(user_id, duration_days=30)

        await callback.answer("✅ Premium-статус выдан на 30 дней!", show_alert=True)

        user = await async_db_manager.get_user_profile(user_id)
        sub = user.subscription
        sub_status = "Активна" if user.is_premium else "Отсутствует"
        if sub and sub.end_date:
            sub_status += f" до {sub.end_date.strftime('%d.%m.%Y')}"

        profile_text = (
            f"👤 **Профиль пользователя**\n\n"
            f"**ID:** `{user.telegram_id}`\n"
            f"**Имя:** {user.name}\n"
            f"**Регистрация:** {user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"**Premium:** {sub_status}\n"
            f"**Профиль завершен:** {'✅' if user.is_profile_complete else '❌'}"
        )
        await callback.message.edit_text(
            profile_text,
            reply_markup=keyboards.user_profile_keyboard(user_id, user.is_premium),
        )

    @router.callback_query(F.data.startswith("revoke_premium_"))
    async def admin_revoke_premium_legacy(
        callback: CallbackQuery
    ):
        """Отзыв Premium-статуса у пользователя (legacy для совместимости)."""
        user_id = int(callback.data.split("_")[-1])
        await async_db_manager.cancel_subscription(user_id)

        await callback.answer("❌ Premium-статус отозван.", show_alert=True)

        user = await async_db_manager.get_user_profile(user_id)
        sub = user.subscription
        sub_status = "Активна" if user.is_premium else "Отсутствует"
        if sub and sub.end_date:
            sub_status += f" до {sub.end_date.strftime('%d.%m.%Y')}"

        profile_text = (
            f"👤 **Профиль пользователя**\n\n"
            f"**ID:** `{user.telegram_id}`\n"
            f"**Имя:** {user.name}\n"
            f"**Регистрация:** {user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"**Premium:** {sub_status}\n"
            f"**Профиль завершен:** {'✅' if user.is_profile_complete else '❌'}"
        )
        await callback.message.edit_text(
            profile_text,
            reply_markup=keyboards.user_profile_keyboard(user_id, user.is_premium),
        )

    @router.callback_query(F.data.startswith("view_charts_"))
    async def admin_view_user_charts(
        callback: CallbackQuery
    ):
        """Просмотр натальных карт пользователя."""
        user_id = int(callback.data.split("_")[-1])
        charts = await async_db_manager.get_user_charts(user_id)

        if not charts:
            text = "📋 У пользователя нет натальных карт."
        else:
            text = f"📋 **Натальные карты пользователя** ({len(charts)} шт.)\n\n"
            for chart in charts[:5]:  # Показываем только первые 5
                chart_type = "👤 Своя" if chart.chart_type == "own" else "👥 Чужая"
                text += f"{chart_type} - {chart.city}\n"
                text += f"📅 {chart.birth_date.strftime('%d.%m.%Y %H:%M')}\n\n"

        await callback.message.edit_text(
            text, reply_markup=keyboards.back_to_main_admin_keyboard()
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("view_activity_"))
    async def admin_view_user_activity(
        callback: CallbackQuery
    ):
        """Просмотр активности пользователя."""
        user_id = int(callback.data.split("_")[-1])
        activity = await async_db_manager.get_user_activity(user_id)

        if not activity:
            text = "❌ Данные об активности не найдены."
        else:
            text = (
                f"📊 **Активность пользователя**\n\n"
                f"📋 Натальных карт: {activity['charts_count']}\n"
                f"🔮 Прогнозов: {activity['predictions_count']}\n"
                f"📅 Регистрация: {activity['registration_date'].strftime('%d.%m.%Y')}\n"
                f"✅ Профиль завершен: {'Да' if activity['profile_complete'] else 'Нет'}\n"
                f"🔔 Уведомления: {'Включены' if activity['notifications_enabled'] else 'Отключены'}"
            )

            if activity["last_chart_date"]:
                text += f"\n📋 Последняя карта: {activity['last_chart_date'].strftime('%d.%m.%Y')}"
            if activity["last_prediction_date"]:
                text += f"\n🔮 Последний прогноз: {activity['last_prediction_date'].strftime('%d.%m.%Y')}"

        await callback.message.edit_text(
            text, reply_markup=keyboards.back_to_main_admin_keyboard()
        )
        await callback.answer()

    # === РАССЫЛКИ (существующий функционал) ===

    @router.callback_query(F.data == "admin_mailing")
    async def admin_mailing_start(callback: CallbackQuery, state: FSMContext):
        """Начало процесса рассылки."""
        await state.set_state(AdminStates.mailing_message_input)
        await callback.message.edit_text(
            "📣 **Создание рассылки**\n\nОтправьте сообщение для рассылки всем пользователям:",
            reply_markup=keyboards.back_to_main_admin_keyboard(),
        )
        await callback.answer()

    @router.message(AdminStates.mailing_message_input)
    async def admin_mailing_get_message(
        message: Message, state: FSMContext
    ):
        """Получение сообщения для рассылки и запрос подтверждения."""
        await state.update_data(message_to_send=message.model_dump())

        total_users = await async_db_manager.get_total_users_count()

        await message.answer("📋 **Предпросмотр сообщения:**")
        await message.answer(
            f"📝 **Текст:**\n{message.text}\n\n"
            f"📊 **Будет отправлено:** {total_users} пользователям",
            reply_markup=keyboards.mailing_confirmation_keyboard(),
        )

    @router.callback_query(F.data == "mailing_send", AdminStates.mailing_message_input)
    async def admin_mailing_confirm(
        callback: CallbackQuery,
        state: FSMContext,
        bot: Bot,
    ):
        """Подтверждение отправки рассылки."""
        data = await state.get_data()
        message_info = data.get("message_to_send")

        if not message_info:
            await callback.answer("❌ Сообщение не найдено.", show_alert=True)
            await state.clear()
            return

        # Запускаем отправку в фоне
        asyncio.create_task(
            send_mailing_to_users(bot, async_db_manager, message_info, callback.from_user.id)
        )

        await callback.answer("✅ Рассылка запущена!", show_alert=True)
        await callback.message.edit_text(
            "✅ **Рассылка запущена**\n\n📤 Сообщения отправляются в фоновом режиме.",
            reply_markup=keyboards.back_to_main_admin_keyboard(),
        )
        await state.clear()

    @router.callback_query(
        F.data == "mailing_cancel", AdminStates.mailing_message_input
    )
    async def admin_mailing_cancel(callback: CallbackQuery, state: FSMContext):
        """Отмена рассылки."""
        await state.clear()
        await callback.answer("❌ Рассылка отменена.", show_alert=True)
        await callback.message.edit_text(
            "❌ **Рассылка отменена**",
            reply_markup=keyboards.back_to_main_admin_keyboard(),
        )

    async def send_mailing_to_users(
        bot: Bot, db_manager: DatabaseManager, message_info: dict, admin_id: int
    ):
        """Фоновая задача для отправки сообщений."""
        logger.info(f"🚀 Начинаем рассылку. Админ ID: {admin_id}")
        
        users = await async_db_manager.get_users_for_mailing()
        logger.info(f"📋 Получено {len(users)} пользователей для рассылки")
        
        message = Message.model_validate(message_info)
        logger.info(f"📝 Текст сообщения: {message.text[:50]}...")

        success_count = 0
        error_count = 0
        error_details = []

        for i, user in enumerate(users, 1):
            logger.info(f"📤 [{i}/{len(users)}] Отправляем сообщение пользователю {user.telegram_id} ({user.name})")
            
            try:
                # Безопасно получаем parse_mode, если его нет - используем None
                parse_mode = getattr(message, 'parse_mode', None)
                
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message.text,
                    parse_mode=parse_mode,
                )
                success_count += 1
                logger.info(f"✅ Сообщение успешно отправлено пользователю {user.telegram_id}")
                await asyncio.sleep(0.05)  # Небольшая задержка между сообщениями
            except Exception as e:
                error_count += 1
                error_msg = f"Ошибка отправки сообщения пользователю {user.telegram_id}: {e}"
                logger.error(error_msg)
                error_details.append(f"Пользователь {user.telegram_id}: {e}")
                
                # Логируем конкретные типы ошибок
                if "Forbidden" in str(e):
                    logger.warning(f"Пользователь {user.telegram_id} заблокировал бота")
                elif "user not found" in str(e).lower():
                    logger.warning(f"Пользователь {user.telegram_id} не найден")
                elif "chat not found" in str(e).lower():
                    logger.warning(f"Чат с пользователем {user.telegram_id} не найден")

        logger.info(f"📊 Рассылка завершена. Успешно: {success_count}, Ошибок: {error_count}")
        
        # Отправляем отчет админу
        try:
            report_text = f"📊 **Рассылка завершена**\n\n"
            report_text += f"✅ Успешно отправлено: {success_count}\n"
            report_text += f"❌ Ошибок: {error_count}\n"
            report_text += f"📤 Всего получателей: {len(users)}"
            
            if error_details:
                report_text += f"\n\n🔍 **Детали ошибок:**\n"
                for detail in error_details[:5]:  # Показываем первые 5 ошибок
                    report_text += f"• {detail}\n"
                if len(error_details) > 5:
                    report_text += f"• ... и еще {len(error_details) - 5} ошибок"
            
            await bot.send_message(chat_id=admin_id, text=report_text)
            logger.info(f"✅ Отчет отправлен админу {admin_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки отчета админу {admin_id}: {e}")

    # === БАЗОВАЯ СТАТИСТИКА ===

    @router.callback_query(F.data == "admin_stats")
    async def admin_stats_show(callback: CallbackQuery):
        """Отображение базовой статистики."""
        stats = await async_db_manager.get_app_statistics()

        stats_text = (
            f"📊 **Статистика приложения**\n\n"
            f"👥 **Пользователи:**\n"
            f"  • Всего: {stats['total_users']}\n"
            f"  • Сегодня: +{stats['new_users_today']}\n"
            f"  • За неделю: +{stats['new_users_7_days']}\n"
            f"  • За месяц: +{stats['new_users_30_days']}\n\n"
            f"💎 **Premium:** {stats['active_premium']} активных\n"
            f"📊 **Карты:** {stats['total_charts']} всего"
        )
        await callback.message.edit_text(stats_text, reply_markup=keyboards.back_to_main_admin_keyboard())
        await callback.answer()

    @router.callback_query(F.data.startswith("send_message_"))
    async def admin_send_message_start(callback: CallbackQuery, state: FSMContext):
        """Начало отправки сообщения пользователю из админки."""
        user_id = int(callback.data.split("_")[-1])
        await state.update_data(target_user_id=user_id)
        await state.set_state(AdminStates.send_message_input)
        await callback.message.edit_text(
            f"💬 Введите текст сообщения для пользователя <code>{user_id}</code>:",
            reply_markup=keyboards.back_to_main_admin_keyboard(),
        )
        await callback.answer()

    @router.message(AdminStates.send_message_input)
    async def admin_send_message_finish(message: Message, state: FSMContext, bot: Bot):
        """Получение текста сообщения и отправка пользователю."""
        data = await state.get_data()
        user_id = data.get("target_user_id")
        if not user_id:
            await message.answer("❌ Не удалось определить пользователя.")
            await state.clear()
            return
        try:
            await bot.send_message(chat_id=user_id, text=message.text)
            await message.answer(f"✅ Сообщение отправлено пользователю <code>{user_id}</code>!", reply_markup=keyboards.back_to_main_admin_keyboard())
        except Exception as e:
            await message.answer(f"❌ Не удалось отправить сообщение: {e}", reply_markup=keyboards.back_to_main_admin_keyboard())
        await state.clear()

    # === ОБРАБОТКА НЕИЗВЕСТНЫХ CALLBACK ===

    @router.callback_query(F.data == "noop")
    async def admin_noop(callback: CallbackQuery):
        """Обработка пустых callback (например, для отображения номера страницы)."""
        await callback.answer()

    return router
