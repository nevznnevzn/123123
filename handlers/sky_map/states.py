from aiogram.fsm.state import State, StatesGroup


class SkyMapStates(StatesGroup):
    """Состояния для создания карт звездного неба"""

    # Состояния для чужой карты
    waiting_for_other_name = State()
    waiting_for_other_date = State()
    waiting_for_other_time = State()
    waiting_for_other_city = State()
