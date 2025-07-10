from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class StarAdviceKeyboards:
    """Клавиатуры для Звёздного совета"""

    @staticmethod
    def categories_menu() -> InlineKeyboardMarkup:
        """Главное меню категорий для вопросов"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💼 Работа и карьера", callback_data="star_advice_career"
                    ),
                    InlineKeyboardButton(
                        text="❤️ Отношения и любовь", callback_data="star_advice_love"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="💰 Финансы и ресурсы",
                        callback_data="star_advice_finances",
                    ),
                    InlineKeyboardButton(
                        text="🏠 Семья и дом", callback_data="star_advice_family"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🌱 Личностный рост", callback_data="star_advice_growth"
                    ),
                    InlineKeyboardButton(
                        text="✍️ Другой вопрос", callback_data="star_advice_other"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад в меню", callback_data="back_to_main"
                    )
                ],
            ]
        )
        return keyboard

    @staticmethod
    def back_to_categories() -> InlineKeyboardMarkup:
        """Кнопка возврата к категориям"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 К выбору категории", callback_data="star_advice_back"
                    )
                ]
            ]
        )
        return keyboard

    @staticmethod
    def cooldown_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура при активном кулдауне"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 В главное меню", callback_data="back_to_main"
                    )
                ]
            ]
        )
        return keyboard

    @staticmethod
    def limit_reached_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура при достижении лимита"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💎 Получить Premium", callback_data="get_premium"
                    ),
                    InlineKeyboardButton(
                        text="🔙 В меню", callback_data="back_to_main"
                    ),
                ]
            ]
        )
        return keyboard
