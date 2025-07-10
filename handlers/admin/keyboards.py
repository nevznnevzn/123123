from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_admin_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админ-панели."""
    buttons = [
        [InlineKeyboardButton(text="👤 Пользователи", callback_data="admin_users")],
        [
            InlineKeyboardButton(
                text="💎 Управление подписками", callback_data="admin_subscriptions"
            )
        ],
        [InlineKeyboardButton(text="📣 Рассылки", callback_data="admin_mailing")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="⚙️ Система", callback_data="admin_system")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_main_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для возврата в главное меню админки."""
    buttons = [
        [
            InlineKeyboardButton(
                text="⬅️ Назад в админ-панель", callback_data="admin_panel"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def users_management_keyboard() -> InlineKeyboardMarkup:
    """Меню управления пользователями."""
    buttons = [
        [
            InlineKeyboardButton(
                text="🔍 Поиск пользователя", callback_data="admin_user_search"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Список всех пользователей", callback_data="admin_users_list"
            )
        ],
        [
            InlineKeyboardButton(
                text="👥 Активные пользователи", callback_data="admin_active_users"
            )
        ],
        [
            InlineKeyboardButton(
                text="💎 Премиум пользователи", callback_data="admin_premium_users"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑️ Удалить пользователя", callback_data="admin_delete_user"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад в главное меню", callback_data="admin_panel"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def subscriptions_management_keyboard() -> InlineKeyboardMarkup:
    """Меню управления подписками."""
    buttons = [
        [
            InlineKeyboardButton(
                text="💎 Выдать Premium", callback_data="admin_grant_premium"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отозвать Premium", callback_data="admin_revoke_premium"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Статистика подписок", callback_data="admin_sub_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Массовое продление", callback_data="admin_bulk_extend"
            )
        ],
        [
            InlineKeyboardButton(
                text="🧹 Очистить истекшие", callback_data="admin_cleanup_expired"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад в главное меню", callback_data="admin_panel"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def system_management_keyboard() -> InlineKeyboardMarkup:
    """Меню системного управления."""
    buttons = [
        [InlineKeyboardButton(text="🧹 Очистка БД", callback_data="admin_cleanup_db")],
        [
            InlineKeyboardButton(
                text="📈 Подробная статистика", callback_data="admin_detailed_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔧 Техническая информация", callback_data="admin_tech_info"
            )
        ],
        [
            InlineKeyboardButton(
                text="📤 Экспорт данных", callback_data="admin_export_data"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад в главное меню", callback_data="admin_panel"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def user_profile_keyboard(user_id: int, is_premium: bool) -> InlineKeyboardMarkup:
    """Клавиатура для профиля пользователя в админ-панели."""
    buttons = []
    if is_premium:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="❌ Забрать Premium", callback_data=f"revoke_premium_{user_id}"
                )
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text="⏰ Продлить Premium",
                    callback_data=f"extend_premium_{user_id}",
                )
            ]
        )
    else:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="✅ Выдать Premium (30 дн.)",
                    callback_data=f"grant_premium_{user_id}",
                )
            ]
        )

    buttons.extend(
        [
            [
                InlineKeyboardButton(
                    text="📋 Натальные карты", callback_data=f"view_charts_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Активность", callback_data=f"view_activity_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Отправить сообщение",
                    callback_data=f"send_message_{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Удалить пользователя",
                    callback_data=f"delete_user_{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к пользователям", callback_data="admin_users"
                )
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def premium_duration_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора срока Premium подписки."""
    buttons = [
        [InlineKeyboardButton(text="7 дней", callback_data=f"premium_7_{user_id}")],
        [InlineKeyboardButton(text="30 дней", callback_data=f"premium_30_{user_id}")],
        [InlineKeyboardButton(text="90 дней", callback_data=f"premium_90_{user_id}")],
        [InlineKeyboardButton(text="365 дней", callback_data=f"premium_365_{user_id}")],
        [
            InlineKeyboardButton(
                text="Бессрочно", callback_data=f"premium_unlimited_{user_id}"
            )
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_subscriptions")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def user_list_navigation_keyboard(
    page: int, total_pages: int, list_type: str = "all"
) -> InlineKeyboardMarkup:
    """Клавиатура навигации по списку пользователей."""
    buttons = []

    # Навигационные кнопки
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️", callback_data=f"users_page_{list_type}_{page-1}"
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop")
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️", callback_data=f"users_page_{list_type}_{page+1}"
            )
        )

    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад к пользователям", callback_data="admin_users"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_action_keyboard(action: str, target_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия."""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Да, подтвердить", callback_data=f"confirm_{action}_{target_id}"
            )
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def bulk_premium_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для массового управления Premium."""
    buttons = [
        [
            InlineKeyboardButton(
                text="30 дней всем активным", callback_data="bulk_premium_30_active"
            )
        ],
        [
            InlineKeyboardButton(
                text="7 дней новым пользователям", callback_data="bulk_premium_7_new"
            )
        ],
        [
            InlineKeyboardButton(
                text="Продлить истекающие", callback_data="bulk_extend_expiring"
            )
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_subscriptions")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def mailing_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения рассылки."""
    buttons = [
        [InlineKeyboardButton(text="✅ Отправить", callback_data="mailing_send")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="mailing_cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
