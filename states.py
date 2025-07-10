from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    """Состояния для настройки профиля пользователя."""

    waiting_for_name = State()
    waiting_for_gender = State()
    waiting_for_city = State()
    waiting_for_birth_date = State()


class AstroStates(StatesGroup):
    # --- Общие состояния ---
    waiting_for_city = State()
    waiting_for_birth_date = State()

    # --- Состояния для натальной карты (чужой) ---
    waiting_for_other_name = State()
    waiting_for_other_city = State()
    waiting_for_other_birth_date = State()

    # --- Состояния для совместимости ---
    waiting_for_partner_name = State()
    waiting_for_partner_city = State()
    waiting_for_partner_birth_date = State()
    waiting_for_compatibility_sphere = State()
