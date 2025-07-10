from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class SkyMapKeyboards:
    """Клавиатуры для звездного неба"""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Главное меню звездного неба"""
        keyboard = [
            [InlineKeyboardButton(text="✨ Готов(а)", callback_data="my_sky")],
            [
                InlineKeyboardButton(
                    text="👥 Небо другого человека", callback_data="other_sky"
                )
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def sky_actions() -> InlineKeyboardMarkup:
        """Действия после создания карты неба"""
        keyboard = [
            [
                InlineKeyboardButton(
                    text="🔄 Создать другую карту", callback_data="create_another_sky"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌌 Меню звездного неба", callback_data="back_to_sky_menu"
                )
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def back_to_main() -> InlineKeyboardMarkup:
        """Возврат в главное меню"""
        keyboard = [
            [
                InlineKeyboardButton(
                    text="🌌 Меню звездного неба", callback_data="back_to_sky_menu"
                )
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def skip_time() -> InlineKeyboardMarkup:
        """Пропустить ввод времени"""
        keyboard = [
            [
                InlineKeyboardButton(
                    text="⏰ Использовать 12:00", callback_data="skip_time"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌌 Меню звездного неба", callback_data="back_to_sky_menu"
                )
            ],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
