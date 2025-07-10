from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    user_search = State()  # Ожидание ID пользователя для поиска
    mailing_message_input = State()  # Ожидание сообщения для рассылки
    mailing_confirmation = State()  # Ожидание подтверждения рассылки

    # Новые состояния для расширенного функционала
    premium_user_search = State()  # Поиск пользователя для выдачи Premium
    revoke_user_search = State()  # Поиск пользователя для отзыва Premium
    delete_user_search = State()  # Поиск пользователя для удаления
    send_message_input = State()  # Ввод сообщения для отправки пользователю
    bulk_premium_confirmation = State()  # Подтверждение массовой выдачи Premium
