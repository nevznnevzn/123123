from aiogram.fsm.state import State, StatesGroup


class StarAdviceStates(StatesGroup):
    """Состояния для Звёздного совета"""

    waiting_for_question = State()  # Ожидание вопроса от пользователя
    processing_question = State()  # Обработка и анализ вопроса
