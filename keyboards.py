from typing import List

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class Keyboards:
    """Клавиатуры для бота"""

    @staticmethod
    def main_menu(has_charts: bool = False) -> ReplyKeyboardMarkup:
        """Главное меню"""
        main_button_text = "📊 Натальные карты"

        keyboard = [
            [KeyboardButton(text=main_button_text), KeyboardButton(text="🔮 Прогнозы")],
            [
                KeyboardButton(text="💞 Совместимость"),
                KeyboardButton(text="🌟 Звёздный совет"),
            ],
            [
                KeyboardButton(text="🌌 Звёздное небо"),
                KeyboardButton(text="👤 Профиль"),
            ],
            [
                KeyboardButton(text="💎 Подписка"),
            ],
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @staticmethod
    def cancel() -> ReplyKeyboardMarkup:
        """Кнопка отмены"""
        keyboard = [[KeyboardButton(text="🔙 Вернуться в главное меню")]]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @staticmethod
    def time_options() -> ReplyKeyboardMarkup:
        """Варианты указания времени"""
        keyboard = [
            [KeyboardButton(text="✅ Продолжить без времени (12:00)")],
            [KeyboardButton(text="🔙 Вернуться в главное меню")],
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @staticmethod
    def profile_time_options() -> ReplyKeyboardMarkup:
        """Варианты указания времени для профиля"""
        keyboard = [
            [KeyboardButton(text="✅ Сохранить без времени (12:00)")],
            [KeyboardButton(text="🔙 Вернуться в главное меню")],
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @staticmethod
    def profile_time_options_no_cancel() -> ReplyKeyboardMarkup:
        """Варианты указания времени для профиля без кнопки отмены"""
        keyboard = [[KeyboardButton(text="✅ Сохранить без времени (12:00)")]]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @staticmethod
    def planets_from_data(
        all_planets: List[str], user_planets: dict, current_planet: str = None
    ) -> InlineKeyboardMarkup:
        """Клавиатура с кнопками ВСЕХ планет из JSON файла"""
        builder = InlineKeyboardBuilder()

        # Убираем Асцендент из списка если он есть и добавляем кнопки для всех планет кроме Асцендента
        planets_without_asc = [p for p in all_planets if p != "Асцендент"]

        for planet_name in planets_without_asc:
            # Если это текущая планета, добавляем "(вернуться назад)"
            if planet_name == current_planet:
                button_text = f"{planet_name} (вернуться назад)"
            else:
                button_text = f"{planet_name}"

            builder.add(
                InlineKeyboardButton(
                    text=button_text, callback_data=f"planet_{planet_name}"
                )
            )

        # Добавляем Асцендент последним, если он есть в данных пользователя
        if "Асцендент" in user_planets:
            # Если это текущая планета, добавляем "(вернуться назад)"
            if "Асцендент" == current_planet:
                button_text = "Асцендент (вернуться назад)"
            else:
                button_text = "Асцендент"

            builder.add(
                InlineKeyboardButton(
                    text=button_text, callback_data=f"planet_Асцендент"
                )
            )

        # Размещаем по 2 кнопки в ряд
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def planets(
        planet_names: List[str], chart_id: int, is_premium: bool = True
    ) -> InlineKeyboardMarkup:
        """Клавиатура с планетами."""
        builder = InlineKeyboardBuilder()

        # Группируем планеты по 2 в ряд
        buttons_in_row = 2
        for i in range(0, len(planet_names), buttons_in_row):
            row_planets = planet_names[i : i + buttons_in_row]
            buttons = [
                InlineKeyboardButton(
                    text=planet, callback_data=f"planet_{chart_id}_{planet}"
                )
                for planet in row_planets
            ]
            builder.row(*buttons)

        # Добавляем кнопку Premium для бесплатных пользователей
        if not is_premium:
            builder.row(
                InlineKeyboardButton(
                    text="💎 Получить Premium - анализ всех планет",
                    callback_data="upgrade_to_premium",
                )
            )

        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад к списку карт", callback_data="back_to_charts_list"
            )
        )
        return builder.as_markup()

    @staticmethod
    def natal_charts_list(charts) -> InlineKeyboardMarkup:
        """Клавиатура со списком натальных карт пользователя"""
        builder = InlineKeyboardBuilder()

        # Добавляем кнопки для каждой натальной карты
        for chart in charts:
            # Определяем префикс для типа карты
            chart_prefix = "👤" if chart.chart_type == "own" else "👥"

            # Формируем название карты
            if chart.chart_type == "own":
                chart_name = f"{chart_prefix} {chart.city} - {chart.birth_date.strftime('%d.%m.%Y')}"
            else:
                owner_name = chart.chart_owner_name or "Неизвестно"
                chart_name = f"{chart_prefix} {owner_name} ({chart.city}) - {chart.birth_date.strftime('%d.%m.%Y')}"

            if chart.has_warning:
                chart_name += " ⚠️"

            builder.add(
                InlineKeyboardButton(text=chart_name, callback_data=f"chart_{chart.id}")
            )

        # Добавляем кнопку "Создать новую"
        builder.add(
            InlineKeyboardButton(
                text="➕ Создать новую натальную карту",
                callback_data="select_chart_type",
            )
        )

        # Размещаем по 1 кнопке в ряд
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def chart_actions(chart_id: int) -> InlineKeyboardMarkup:
        """Клавиатура с действиями для натальной карты"""
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(
                text="👁️ Открыть", callback_data=f"open_chart_{chart_id}"
            )
        )

        builder.add(
            InlineKeyboardButton(
                text="🗑️ Удалить", callback_data=f"delete_chart_{chart_id}"
            )
        )

        builder.add(
            InlineKeyboardButton(
                text="🔙 Назад к списку", callback_data="back_to_charts_list"
            )
        )

        # Размещаем по 2 кнопки в ряд, кроме последней
        builder.adjust(2, 1)
        return builder.as_markup()

    @staticmethod
    def confirm_delete(chart_id: int) -> InlineKeyboardMarkup:
        """Клавиатура подтверждения удаления"""
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(
                text="✅ Да, удалить", callback_data=f"confirm_delete_chart_{chart_id}"
            )
        )

        builder.add(
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"chart_{chart_id}")
        )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def prediction_types(chart_id: int) -> InlineKeyboardMarkup:
        """Клавиатура выбора типа прогноза"""
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(
                text="📅 Прогноз на сегодня",
                callback_data=f"prediction_сегодня_{chart_id}",
            )
        )

        builder.add(
            InlineKeyboardButton(
                text="📆 Прогноз на неделю",
                callback_data=f"prediction_неделя_{chart_id}",
            )
        )

        builder.add(
            InlineKeyboardButton(
                text="🗓️ Прогноз на месяц", callback_data=f"prediction_месяц_{chart_id}"
            )
        )

        builder.add(
            InlineKeyboardButton(
                text="📊 Прогноз на квартал",
                callback_data=f"prediction_квартал_{chart_id}",
            )
        )

        builder.adjust(1)

        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад к выбору карты", callback_data=f"back_to_pred_charts"
            )
        )

        return builder.as_markup()

    @staticmethod
    def prediction_menu_with_existing(
        chart_id: int, existing_predictions: list = None
    ) -> InlineKeyboardMarkup:
        """Клавиатура с активными прогнозами и возможностью создать новые"""
        builder = InlineKeyboardBuilder()

        # Если есть активные прогнозы, показываем их
        if existing_predictions:
            type_names = {
                "сегодня": "📅 На сегодня",
                "неделя": "📆 На неделю",
                "месяц": "🗓️ На месяц",
                "квартал": "📊 На квартал",
            }

            builder.add(
                InlineKeyboardButton(
                    text="📋 Ваши активные прогнозы:",
                    callback_data="dummy_header",  # Неактивная кнопка-заголовок
                )
            )

            for prediction in existing_predictions:
                pred_type = prediction.prediction_type
                type_name = type_names.get(pred_type, pred_type)

                # Кнопка для просмотра существующего прогноза
                builder.add(
                    InlineKeyboardButton(
                        text=f"👁️ {type_name}",
                        callback_data=f"view_prediction_{prediction.id}",
                    )
                )

            # Разделитель
            builder.add(
                InlineKeyboardButton(
                    text="➕ Создать новый прогноз:",
                    callback_data="dummy_create_header",  # Неактивная кнопка-заголовок
                )
            )

        # Кнопки для создания новых прогнозов
        all_types = ["сегодня", "неделя", "месяц", "квартал"]
        existing_types = [p.prediction_type for p in (existing_predictions or [])]

        type_names = {
            "сегодня": "📅 На сегодня",
            "неделя": "📆 На неделю",
            "месяц": "🗓️ На месяц",
            "квартал": "📊 На квартал",
        }

        for pred_type in all_types:
            type_name = type_names[pred_type]

            if pred_type in existing_types:
                # Если прогноз уже есть, показываем кнопку с пометкой
                builder.add(
                    InlineKeyboardButton(
                        text=f" {type_name} (просмотреть)",
                        callback_data=f"prediction_{pred_type}_{chart_id}",
                    )
                )
            else:
                # Если прогноза нет, обычная кнопка
                builder.add(
                    InlineKeyboardButton(
                        text=f"➕ {type_name}",
                        callback_data=f"prediction_{pred_type}_{chart_id}",
                    )
                )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def prediction_charts_list(charts) -> InlineKeyboardMarkup:
        """Клавиатура выбора натальной карты для прогноза"""
        builder = InlineKeyboardBuilder()

        # Добавляем кнопки для каждой натальной карты
        for chart in charts:
            # Определяем префикс для типа карты
            chart_prefix = "👤" if chart.chart_type == "own" else "👥"

            # Формируем название карты
            if chart.chart_type == "own":
                chart_name = f"{chart_prefix} Ваша карта ({chart.city}) - {chart.birth_date.strftime('%d.%m.%Y')}"
            else:
                owner_name = chart.chart_owner_name or "Неизвестно"
                chart_name = f"{chart_prefix} {owner_name} ({chart.city}) - {chart.birth_date.strftime('%d.%m.%Y')}"

            if chart.has_warning:
                chart_name += " ⚠️"

            builder.add(
                InlineKeyboardButton(
                    text=chart_name, callback_data=f"predict_chart_{chart.id}"
                )
            )

        # Добавляем кнопку возврата в главное меню (всегда)
        builder.add(
            InlineKeyboardButton(
                text="🔙 Назад в главное меню", callback_data="back_to_main_menu"
            )
        )

        # Размещаем по 1 кнопке в ряд
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def setup_profile() -> ReplyKeyboardMarkup:
        """Меню настройки профиля"""
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="⚙️ Настроить профиль"))
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def gender_selection() -> InlineKeyboardMarkup:
        """Клавиатура выбора пола"""
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(text="👨 Мужской", callback_data="gender_male")
        )

        builder.add(
            InlineKeyboardButton(text="👩 Женский", callback_data="gender_female")
        )

        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def chart_type_selection() -> InlineKeyboardMarkup:
        """Клавиатура выбора типа натальной карты"""
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(
                text="👤 Моя натальная карта", callback_data="chart_type_own"
            )
        )

        builder.add(
            InlineKeyboardButton(
                text="👥 Чужая натальная карта", callback_data="chart_type_other"
            )
        )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def profile_menu(notifications_enabled: bool) -> InlineKeyboardMarkup:
        """Меню управления профилем"""
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(
                text="✏️ Редактировать данные", callback_data="edit_profile"
            )
        )

        # Кнопка для управления уведомлениями
        if notifications_enabled:
            notification_text = "🔔 Уведомления: Вкл"
        else:
            notification_text = "🔕 Уведомления: Выкл"

        builder.add(
            InlineKeyboardButton(
                text=notification_text, callback_data="toggle_notifications"
            )
        )

        builder.add(
            InlineKeyboardButton(
                text="🔙 Назад в главное меню", callback_data="back_to_main_menu"
            )
        )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def prediction_action_choice(
        chart_id: int, active_predictions_count: int
    ) -> InlineKeyboardMarkup:
        """Меню выбора действия с прогнозами (просмотр/создание)"""
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(
                text=f"👁️ Посмотреть активные прогнозы ({active_predictions_count})",
                callback_data=f"view_active_predictions_{chart_id}",
            )
        )

        builder.add(
            InlineKeyboardButton(
                text="➕ Создать новый прогноз",
                callback_data=f"create_new_prediction_{chart_id}",
            )
        )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def view_active_predictions_menu(
        chart_id: int, existing_predictions: list
    ) -> InlineKeyboardMarkup:
        """Клавиатура для просмотра активных прогнозов"""
        builder = InlineKeyboardBuilder()

        type_names = {
            "сегодня": "📅 На сегодня",
            "неделя": "📆 На неделю",
            "месяц": "🗓️ На месяц",
            "квартал": "📊 На квартал",
        }

        # Кнопки для просмотра существующих прогнозов
        for prediction in existing_predictions:
            pred_type = prediction.prediction_type
            type_name = type_names.get(pred_type, pred_type)

            builder.add(
                InlineKeyboardButton(
                    text=f"👁️ {type_name}",
                    callback_data=f"view_prediction_{prediction.id}",
                )
            )

        # Кнопка "Создать новый"
        builder.add(
            InlineKeyboardButton(
                text="➕ Создать новый прогноз",
                callback_data=f"create_new_prediction_{chart_id}",
            )
        )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def create_new_prediction_menu(
        chart_id: int, existing_predictions: list = None
    ) -> InlineKeyboardMarkup:
        """Клавиатура для создания новых прогнозов"""
        builder = InlineKeyboardBuilder()

        # Кнопки для создания новых прогнозов
        all_types = ["сегодня", "неделя", "месяц", "квартал"]
        existing_types = [p.prediction_type for p in (existing_predictions or [])]

        type_names = {
            "сегодня": "📅 На сегодня",
            "неделя": "📆 На неделю",
            "месяц": "🗓️ На месяц",
            "квартал": "📊 На квартал",
        }

        for pred_type in all_types:
            type_name = type_names[pred_type]

            if pred_type in existing_types:
                # Если прогноз уже есть, показываем кнопку с пометкой
                builder.add(
                    InlineKeyboardButton(
                        text=f" {type_name} (просмотреть)",
                        callback_data=f"prediction_{pred_type}_{chart_id}",
                    )
                )
            else:
                # Если прогноза нет, обычная кнопка
                builder.add(
                    InlineKeyboardButton(
                        text=f"➕ {type_name}",
                        callback_data=f"prediction_{pred_type}_{chart_id}",
                    )
                )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def compatibility_spheres():
        """Клавиатура для выбора сферы совместимости"""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="❤️ Любовь", callback_data="comp_sphere_love")
        )
        builder.add(
            InlineKeyboardButton(
                text="🤝 Дружба", callback_data="comp_sphere_friendship"
            )
        )
        builder.add(
            InlineKeyboardButton(text="📈 Карьера", callback_data="comp_sphere_career")
        )
        builder.add(
            InlineKeyboardButton(
                text="🔙 Назад в главное меню", callback_data="back_to_main_menu"
            )
        )
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def compatibility_reports_list(reports: List) -> InlineKeyboardMarkup:
        """Клавиатура со списком отчетов о совместимости."""
        builder = InlineKeyboardBuilder()
        if reports:
            for report in reports:
                sphere_map = {"love": "❤️", "friendship": "🤝", "career": "📈"}
                sphere_emoji = sphere_map.get(report.sphere, "🔮")
                button_text = f"{sphere_emoji} {report.user_name} & {report.partner_name} ({report.created_at.strftime('%d.%m.%Y')})"
                builder.row(
                    InlineKeyboardButton(
                        text=button_text, callback_data=f"view_comp_report_{report.id}"
                    )
                )

        builder.row(
            InlineKeyboardButton(
                text="➕ Создать новый отчет", callback_data="new_compatibility_report"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад в главное меню", callback_data="back_to_main_menu"
            )
        )
        
        return builder.as_markup()

    @staticmethod
    def compatibility_report_actions(report_id: int) -> InlineKeyboardMarkup:
        """Клавиатура с действиями для отчета о совместимости."""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(
                text="🗑️ Удалить", callback_data=f"delete_comp_report_{report_id}"
            )
        )
        builder.add(
            InlineKeyboardButton(
                text="🔙 Назад к отчетам", callback_data="back_to_comp_reports"
            )
        )
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def confirm_delete_compatibility_report(report_id: int) -> InlineKeyboardMarkup:
        """Клавиатура подтверждения удаления отчета о совместимости."""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(
                text="✅ Да, удалить",
                callback_data=f"confirm_delete_comp_report_{report_id}",
            )
        )
        builder.add(
            InlineKeyboardButton(
                text="❌ Отмена", callback_data=f"view_comp_report_{report_id}"
            )
        )
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def subscription_menu(is_premium: bool = False, days_remaining: int = None) -> InlineKeyboardMarkup:
        """Меню управления подпиской"""
        builder = InlineKeyboardBuilder()

        if is_premium:
            # Для премиум пользователей
            builder.add(
                InlineKeyboardButton(
                    text="📊 Статус подписки", callback_data="subscription_status"
                )
            )
            builder.add(
                InlineKeyboardButton(
                    text="🔄 Продлить подписку", callback_data="subscription_renew"
                )
            )
            builder.add(
                InlineKeyboardButton(
                    text="❌ Отменить подписку", callback_data="subscription_cancel"
                )
            )
        else:
            # Для бесплатных пользователей
            builder.add(
                InlineKeyboardButton(
                    text="💎 Оформить Premium", callback_data="subscription_upgrade"
                )
            )
            builder.add(
                InlineKeyboardButton(
                    text="📋 Что даёт Premium?", callback_data="subscription_benefits"
                )
            )
            builder.add(
                InlineKeyboardButton(
                    text="📊 Мой статус", callback_data="subscription_status"
                )
            )

        builder.add(
            InlineKeyboardButton(
                text="🔙 Назад в главное меню", callback_data="back_to_main"
            )
        )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def subscription_upgrade_options() -> InlineKeyboardMarkup:
        """Варианты оформления подписки"""
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(
                text="💳 Месячная подписка (499₽)", callback_data="buy_monthly"
            )
        )

        builder.add(
            InlineKeyboardButton(
                text="❓ Часто задаваемые вопросы", callback_data="subscription_faq"
            )
        )
        builder.add(
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="subscription_back"
            )
        )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def subscription_confirm_cancel() -> InlineKeyboardMarkup:
        """Подтверждение отмены подписки"""
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(
                text="✅ Да, отменить", callback_data="subscription_cancel_confirm"
            )
        )
        builder.add(
            InlineKeyboardButton(
                text="❌ Нет, оставить", callback_data="subscription_back"
            )
        )

        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def back_to_main_menu():
        """Клавиатура с одной кнопкой 'В главное меню'"""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_main")
        )
        return builder.as_markup()

    @staticmethod
    def skip_step_keyboard():
        """Клавиатура с кнопкой для пропуска шага"""
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="Пропустить шаг (время будет 12:00)"))
        builder.add(KeyboardButton(text="🔙 Вернуться в главное меню"))
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

    @staticmethod
    def back_to_planets(chart_id: int) -> InlineKeyboardMarkup:
        """Клавиатура для возврата к списку планет."""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(
                text="🔙 Назад к планетам", callback_data=f"open_chart_{chart_id}"
            )
        )
        return builder.as_markup()

    @staticmethod
    def back_to_chart_predictions(chart_id: int) -> InlineKeyboardMarkup:
        """Клавиатура для возврата к списку прогнозов карты"""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(
                text="🔙 Назад к прогнозам",
                callback_data=f"back_to_chart_predictions_{chart_id}",
            )
        )
        builder.add(
            InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_main")
        )
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def premium_upgrade() -> InlineKeyboardMarkup:
        """Клавиатура для оформления Premium подписки"""
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(
                text="💎 Оформить Premium за 199₽/месяц",
                callback_data="subscribe_premium_monthly",
            )
        )

        builder.add(
            InlineKeyboardButton(
                text="💎 Оформить Premium за 1990₽/год (скидка 17%)",
                callback_data="subscribe_premium_yearly",
            )
        )

        builder.add(
            InlineKeyboardButton(
                text="ℹ️ Подробнее о Premium", callback_data="premium_info"
            )
        )

        builder.add(
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_charts_list")
        )

        builder.adjust(1)
        return builder.as_markup()
