from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    FSInputFile,
    MenuButtonCommands,
    Message,
    ReplyKeyboardRemove,
)

from database import db_manager
from keyboards import Keyboards
from states import AstroStates

router = Router()


async def setup_bot_commands(bot: Bot):
    """Настройка команд бота и кнопки меню"""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="menu", description="📋 Главное меню"),
        BotCommand(command="reset_data", description="🗑️ Удалить все данные (отладка)"),
    ]
    await bot.set_my_commands(commands)
    menu_button = MenuButtonCommands()
    await bot.set_chat_menu_button(menu_button=menu_button)


def format_charts_count_bold(count: int) -> str:
    """Форматированное склонение с жирным начертанием числа"""
    last_digit = count % 10
    last_two_digits = count % 100
    if 11 <= last_two_digits <= 14:
        return f"<b>{count}</b> сохраненных натальных карт"
    if last_digit == 1:
        return f"<b>{count}</b> сохраненная натальная карта"
    if 2 <= last_digit <= 4:
        return f"<b>{count}</b> сохраненные натальные карты"
    return f"<b>{count}</b> сохраненных натальных карт"


def get_main_menu(user_id: int):
    """Получить главное меню в зависимости от завершенности профиля пользователя"""
    user_profile = db_manager.get_user_profile(user_id)
    if not user_profile or not user_profile.is_profile_complete:
        return Keyboards.setup_profile()
    return Keyboards.main_menu()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    user, created = db_manager.get_or_create_user(
        telegram_id=message.from_user.id, name=message.from_user.full_name
    )

    if created or not user.is_profile_complete:
        # Если пользователь новый или профиль не завершен
        text = (
            f"👋 <b>Добро пожаловать, {message.from_user.first_name}!</b>\n\n"
            "Я — ваш личный астрологический помощник, бот <b>Solar Balance</b> 🔮\n\n"
            "Чтобы я мог составлять для вас точные натальные карты и персональные прогнозы, "
            "пожалуйста, сначала настройте свой профиль."
        )
        await message.answer_photo(
            photo="https://i.imgur.com/your-image.png",  # Замените на реальную ссылку
            caption=text,
            reply_markup=Keyboards.setup_profile(),
        )
    else:
        # Если пользователь вернулся и профиль заполнен
        has_charts = len(db_manager.get_user_charts(user.telegram_id)) > 0
        text = (
            f"🎉 <b>С возвращением, {message.from_user.first_name}!</b>\n\n"
            "Рад снова вас видеть! Чем я могу вам помочь сегодня?"
        )
        await message.answer(text, reply_markup=Keyboards.main_menu(has_charts))


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    """Обработчик команды /menu"""
    await state.clear()

    user_id = message.from_user.id
    user_profile = db_manager.get_user_profile(user_id)
    profile_complete = user_profile and user_profile.is_profile_complete

    if not profile_complete:
        text = "📝 <b>Настройка профиля</b> ⚙️\n\nДля доступа к меню необходимо завершить настройку профиля."
    else:
        text = "📋 <b>Главное меню</b> ✨"

    await message.answer(text, reply_markup=get_main_menu(user_id))


@router.message(Command("reset_data"))
async def cmd_reset_data(message: Message):
    """Обработчик команды /reset_data"""
    reset_text = (
        "<b>⚠️ Предупреждение</b>\n\n"
        "Вы уверены, что хотите удалить все свои данные, включая профиль и все натальные карты?\n\n"
        "Это действие необратимо. Для подтверждения нажмите кнопку ниже."
    )
    await message.answer(reset_text, reply_markup=Keyboards.confirm_reset_keyboard())


@router.message(Command("confirm_reset"))
async def cmd_confirm_reset(message: Message):
    """Подтверждение сброса данных"""
    user_id = message.from_user.id
    db_manager.delete_user_data(user_id)

    await message.answer(
        "✅ Все ваши данные были успешно удалены.\n"
        "Чтобы начать заново, введите /start",
        reply_markup=Keyboards.setup_profile(),
    )


@router.message(F.text == "🔙 Вернуться в главное меню")
async def back_to_menu(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()

    user_id = message.from_user.id
    user_profile = db_manager.get_user_profile(user_id)

    if user_profile and user_profile.is_profile_complete:
        text = "📋 <b>Добро пожаловать!</b> ✨\n\nВы вернулись в главное меню."
    else:
        text = "📝 <b>Завершите настройку</b> ⚙️\n\nПожалуйста, завершите настройку профиля."

    await message.answer(text, reply_markup=get_main_menu(user_id))


@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'В главное меню'"""
    await state.clear()

    has_charts = len(db_manager.get_user_charts(callback.from_user.id)) > 0

    await callback.message.edit_text(
        "🔮 <b>Главное меню</b>\n\nВыберите, что вас интересует:", reply_markup=None
    )

    await callback.message.answer(
        "Чем я могу вам помочь?", reply_markup=Keyboards.main_menu(has_charts)
    )

    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'В главное меню' (альтернативный callback)"""
    await state.clear()

    has_charts = len(db_manager.get_user_charts(callback.from_user.id)) > 0

    await callback.message.edit_text(
        "🔮 <b>Главное меню</b>\n\nВыберите, что вас интересует:", reply_markup=None
    )

    await callback.message.answer(
        "Чем я могу вам помочь?", reply_markup=Keyboards.main_menu(has_charts)
    )

    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Главное меню' (для модуля звездного неба)"""
    await state.clear()

    has_charts = len(db_manager.get_user_charts(callback.from_user.id)) > 0

    await callback.message.edit_text(
        "🔮 <b>Главное меню</b>\n\nВыберите, что вас интересует:", reply_markup=None
    )

    await callback.message.answer(
        "Чем я могу вам помочь?", reply_markup=Keyboards.main_menu(has_charts)
    )

    await callback.answer()


@router.callback_query(F.data == "delete_account")
async def delete_account_callback(callback: CallbackQuery):
    """Подтверждение удаления аккаунта"""
    await callback.message.edit_text(
        "Вы уверены, что хотите удалить свой аккаунт и все данные? "
        "Это действие необратимо.",
        reply_markup=Keyboards.confirm_delete_account(),
    )


@router.callback_query(F.data == "confirm_delete_account")
async def confirm_delete_account_callback(callback: CallbackQuery):
    """Окончательное удаление аккаунта"""
    deleted, charts_count = db_manager.delete_user_completely(callback.from_user.id)
    if deleted:
        await callback.message.edit_text(
            f"Ваш аккаунт и {charts_count} натальных карт были успешно удалены. "
            "Надеюсь, вы вернетесь снова!",
            reply_markup=None,
        )
    else:
        await callback.answer("Не удалось удалить аккаунт.", show_alert=True)


@router.message()
async def handle_unknown_message(message: Message, state: FSMContext):
    """Обработчик для неизвестных сообщений."""
    await message.answer(
        "😕 <b>Не понимаю эту команду</b> 🤔\n\n"
        "⭐ Пожалуйста, используйте кнопки меню или введите одну из доступных команд: /start, /help, /menu.",
        reply_markup=get_main_menu(message.from_user.id),
    )


@router.callback_query(F.data.in_(["dummy_header", "dummy_create_header"]))
async def handle_dummy_callbacks(callback: CallbackQuery):
    """Обработка нажатий на неактивные кнопки-заголовки"""
    await callback.answer()
