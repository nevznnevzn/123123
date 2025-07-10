import asyncio
import platform
import sys
from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import DatabaseManager

from . import keyboards
from .states import AdminStates


def create_admin_router() -> Router:
    """Создает и настраивает роутер для админ-панели."""
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
        message: Message, state: FSMContext, db_manager: DatabaseManager
    ):
        """Поиск пользователя по ID."""
        if not message.text.isdigit():
            await message.answer("❌ Некорректный ID. Введите числовой Telegram ID.")
            return

        user_id = int(message.text)
        user = db_manager.get_user_profile(user_id)

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
        db_manager: DatabaseManager = None,
    ):
        """Показать список пользователей с пагинацией."""
        if not db_manager:
            # Получаем db_manager из middleware или создаем новый
            from database import db_manager as default_db_manager

            db_manager = default_db_manager

        users, total_pages = db_manager.get_users_paginated(page, 10, list_type)

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
        message: Message, state: FSMContext, db_manager: DatabaseManager
    ):
        """Пользователь найден, выбор срока Premium."""
        if not message.text.isdigit():
            await message.answer("❌ Некорректный ID. Введите числовой Telegram ID.")
            return

        user_id = int(message.text)
        user = db_manager.get_user_profile(user_id)

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
        callback: CallbackQuery, db_manager: DatabaseManager
    ):
        """Выдача Premium на выбранный срок."""
        parts = callback.data.split("_")
        duration = parts[1]
        user_id = int(parts[2])

        days_map = {"7": 7, "30": 30, "90": 90, "365": 365, "unlimited": None}
        days = days_map.get(duration)

        if days is None:  # Бессрочная подписка
            db_manager.create_premium_subscription(user_id, duration_days=99999)
            duration_text = "бессрочно"
        else:
            db_manager.create_premium_subscription(user_id, duration_days=days)
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
        message: Message, state: FSMContext, db_manager: DatabaseManager
    ):
        """Отзыв Premium подписки."""
        if not message.text.isdigit():
            await message.answer("❌ Некорректный ID. Введите числовой Telegram ID.")
            return

        user_id = int(message.text)
        success = db_manager.cancel_subscription(user_id)

        if success:
            await message.answer("✅ Premium подписка отозвана.")
        else:
            await message.answer(
                "❌ Пользователь не найден или у него нет активной подписки."
            )

        await state.clear()

    @router.callback_query(F.data == "admin_sub_stats")
    async def admin_subscription_stats(
        callback: CallbackQuery, db_manager: DatabaseManager
    ):
        """Статистика подписок."""
        stats = db_manager.get_detailed_statistics()

        text = (
            f"📊 **Статистика подписок**\n\n"
            f"💎 **Активных Premium:** {stats['subscriptions']['active_premium']}\n"
            f"❌ **Истекших Premium:** {stats['subscriptions']['expired_premium']}\n"
            f"📈 **Конверсия:** {stats['subscriptions']['conversion_rate']}%\n\n"
            f"👥 **Всего пользователей:** {stats['users']['total']}"
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
        callback: CallbackQuery, db_manager: DatabaseManager
    ):
        """Массовые действия с Premium."""
        action = callback.data.split("_", 1)[1]

        if action == "premium_30_active":
            # 30 дней всем активным пользователям последние 7 дней
            week_ago = datetime.utcnow() - timedelta(days=7)
            users = db_manager.get_users_paginated(1, 1000, "active")[0]
            count = 0
            for user in users:
                db_manager.create_premium_subscription(
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
            users = db_manager.get_users_paginated(1, 1000, "all")[0]
            count = 0
            for user in users:
                if user.created_at >= today_start:
                    db_manager.create_premium_subscription(
                        user.telegram_id, duration_days=7
                    )
                    count += 1

            await callback.answer(
                f"✅ Premium выдан {count} новым пользователям!", show_alert=True
            )

        elif action == "extend_expiring":
            # Продлить истекающие подписки
            users = db_manager.get_expiring_subscriptions(7)
            count = db_manager.bulk_extend_premium([u.telegram_id for u in users], 30)

            await callback.answer(f"✅ Продлено {count} подписок!", show_alert=True)

        await callback.message.edit_text(
            "✅ **Массовая операция выполнена**",
            reply_markup=keyboards.back_to_main_admin_keyboard(),
        )

    @router.callback_query(F.data == "admin_cleanup_expired")
    async def admin_cleanup_expired(
        callback: CallbackQuery, db_manager: DatabaseManager
    ):
        """Очистка истекших подписок."""
        count = db_manager.check_and_expire_subscriptions()
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
        callback: CallbackQuery, db_manager: DatabaseManager
    ):
        """Подробная статистика."""
        stats = db_manager.get_detailed_statistics()

        text = (
            f"📈 **Подробная статистика**\n\n"
            f"👥 **Пользователи:**\n"
            f"  • Всего: {stats['users']['total']}\n"
            f"  • Сегодня: +{stats['users']['today']}\n"
            f"  • Вчера: +{stats['users']['yesterday']}\n"
            f"  • За неделю: +{stats['users']['week']}\n"
            f"  • За месяц: +{stats['users']['month']}\n\n"
            f"💎 **Подписки:**\n"
            f"  • Активных Premium: {stats['subscriptions']['active_premium']}\n"
            f"  • Истекших: {stats['subscriptions']['expired_premium']}\n"
            f"  • Конверсия: {stats['subscriptions']['conversion_rate']}%\n\n"
            f"📊 **Контент:**\n"
            f"  • Натальных карт: {stats['content']['total_charts']}\n"
            f"  • Карт сегодня: +{stats['content']['charts_today']}\n"
            f"  • Карт за неделю: +{stats['content']['charts_week']}\n"
            f"  • Прогнозов: {stats['content']['total_predictions']}\n"
            f"  • Прогнозов сегодня: +{stats['content']['predictions_today']}\n"
            f"  • Прогнозов за неделю: +{stats['content']['predictions_week']}"
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
        result = db_manager.cleanup_database()

        text = (
            f"🧹 **Очистка базы данных завершена**\n\n"
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
        callback: CallbackQuery, db_manager: DatabaseManager
    ):
        """Выдача Premium-статуса пользователю (legacy для совместимости)."""
        user_id = int(callback.data.split("_")[-1])
        db_manager.create_premium_subscription(user_id, duration_days=30)

        await callback.answer("✅ Premium-статус выдан на 30 дней!", show_alert=True)

        user = db_manager.get_user_profile(user_id)
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
        callback: CallbackQuery, db_manager: DatabaseManager
    ):
        """Отзыв Premium-статуса у пользователя (legacy для совместимости)."""
        user_id = int(callback.data.split("_")[-1])
        db_manager.cancel_subscription(user_id)

        await callback.answer("❌ Premium-статус отозван.", show_alert=True)

        user = db_manager.get_user_profile(user_id)
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
        callback: CallbackQuery, db_manager: DatabaseManager
    ):
        """Просмотр натальных карт пользователя."""
        user_id = int(callback.data.split("_")[-1])
        charts = db_manager.get_user_charts(user_id)

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
        callback: CallbackQuery, db_manager: DatabaseManager
    ):
        """Просмотр активности пользователя."""
        user_id = int(callback.data.split("_")[-1])
        activity = db_manager.get_user_activity(user_id)

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
        message: Message, state: FSMContext, db_manager: DatabaseManager
    ):
        """Получение сообщения для рассылки и запрос подтверждения."""
        await state.update_data(message_to_send=message.model_dump())

        total_users = db_manager.get_total_users_count()

        await message.answer("📋 **Предпросмотр сообщения:**")
        await message.copy_to(chat_id=message.chat.id)
        await message.answer(
            f"📊 Получателей: {total_users} пользователей\n\n❓ Отправить рассылку?",
            reply_markup=keyboards.mailing_confirmation_keyboard(),
        )

    @router.callback_query(F.data == "mailing_send", AdminStates.mailing_message_input)
    async def admin_mailing_confirm(
        callback: CallbackQuery,
        state: FSMContext,
        bot: Bot,
        db_manager: DatabaseManager,
    ):
        """Подтверждение и запуск рассылки."""
        data = await state.get_data()
        message_info = data.get("message_to_send")

        await callback.message.edit_text("⏳ Рассылка началась...")

        asyncio.create_task(
            send_mailing_to_users(
                bot=bot,
                db_manager=db_manager,
                message_info=message_info,
                admin_id=callback.from_user.id,
            )
        )
        await state.clear()
        await callback.answer()

    @router.callback_query(
        F.data == "mailing_cancel", AdminStates.mailing_message_input
    )
    async def admin_mailing_cancel(callback: CallbackQuery, state: FSMContext):
        """Отмена рассылки."""
        await state.clear()
        await callback.message.edit_text(
            "❌ Рассылка отменена.",
            reply_markup=keyboards.back_to_main_admin_keyboard(),
        )
        await callback.answer()

    async def send_mailing_to_users(
        bot: Bot, db_manager: DatabaseManager, message_info: dict, admin_id: int
    ):
        """Фоновая задача для отправки сообщений."""
        users = db_manager.get_users_for_mailing()
        message = Message.model_validate(message_info)

        success_count = 0
        fail_count = 0

        for user in users:
            try:
                await message.copy_to(chat_id=user.telegram_id)
                success_count += 1
                await asyncio.sleep(0.1)
            except Exception:
                fail_count += 1

        report_text = (
            f"✅ **Рассылка завершена!**\n\n"
            f"👍 Доставлено: {success_count}\n"
            f"👎 Не доставлено: {fail_count}"
        )
        await bot.send_message(admin_id, report_text)

    # === БАЗОВАЯ СТАТИСТИКА ===

    @router.callback_query(F.data == "admin_stats")
    async def admin_stats_show(callback: CallbackQuery, db_manager: DatabaseManager):
        """Отображение базовой статистики."""
        stats = db_manager.get_app_statistics()

        stats_text = (
            f"📊 **Базовая статистика**\n\n"
            f"👥 **Пользователи:** {stats['total_users']}\n"
            f"  • Сегодня: +{stats['new_users_today']}\n"
            f"  • За 7 дней: +{stats['new_users_7_days']}\n"
            f"  • За 30 дней: +{stats['new_users_30_days']}\n\n"
            f"💎 **Premium:** {stats['active_premium']}\n"
            f"📋 **Натальных карт:** {stats['total_charts']}"
        )

        await callback.message.edit_text(
            stats_text, reply_markup=keyboards.back_to_main_admin_keyboard()
        )
        await callback.answer()

    # === ОБРАБОТКА НЕИЗВЕСТНЫХ CALLBACK ===

    @router.callback_query(F.data == "noop")
    async def admin_noop(callback: CallbackQuery):
        """Обработка пустых callback (например, для отображения номера страницы)."""
        await callback.answer()

    return router
