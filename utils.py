import calendar
from datetime import datetime, timedelta
from typing import List, Tuple

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat


async def set_bot_commands(bot: Bot, admin_ids: List[int] = None):
    """
    Устанавливает команды для бота в меню Telegram.
    Для обычных пользователей - только /start
    Для админов - только /start и /admin
    """
    # Команды для обычных пользователей (только /start)
    user_commands = [
        BotCommand(command="/start", description="🚀 Запустить бота"),
    ]

    # Команды для админов (только /start и /admin)
    admin_commands = [
        BotCommand(command="/start", description="🚀 Перезапустить бота"),
        BotCommand(command="/admin", description="🔧 Админ-панель"),
    ]

    # Устанавливаем команды по умолчанию для всех пользователей
    await bot.set_my_commands(user_commands, BotCommandScopeDefault())

    # Устанавливаем команды для админов
    if admin_ids:
        for admin_id in admin_ids:
            try:
                await bot.set_my_commands(
                    admin_commands,
                    BotCommandScopeChat(chat_id=admin_id)
                )
            except Exception as e:
                # Игнорируем ошибки для недоступных чатов админов
                print(f"Не удалось установить команды для админа {admin_id}: {e}")


def get_prediction_period(
    prediction_type: str, current_time: datetime = None
) -> Tuple[datetime, datetime]:
    """
    Вычисляет период действия прогноза

    Args:
        prediction_type: Тип прогноза ("сегодня", "неделя", "месяц", "квартал")
        current_time: Текущее время (если None, используется datetime.utcnow())

    Returns:
        Tuple[datetime, datetime]: (начало_периода, конец_периода)
    """
    if current_time is None:
        current_time = datetime.utcnow()

    if prediction_type == "сегодня":
        # Прогноз действует до конца текущего дня
        start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1) - timedelta(microseconds=1)
        return start, end

    elif prediction_type == "неделя":
        # Прогноз действует 7 дней с текущей даты
        start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7) - timedelta(microseconds=1)
        return start, end

    elif prediction_type == "месяц":
        # Прогноз действует до конца текущего месяца
        start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Находим последний день месяца
        year = current_time.year
        month = current_time.month
        last_day = calendar.monthrange(year, month)[1]
        end = current_time.replace(
            day=last_day, hour=23, minute=59, second=59, microsecond=999999
        )

        return start, end

    elif prediction_type == "квартал":
        # Прогноз действует до конца текущего квартала
        year = current_time.year
        month = current_time.month

        # Определяем квартал и его конечный месяц
        if month <= 3:
            quarter_end_month = 3
        elif month <= 6:
            quarter_end_month = 6
        elif month <= 9:
            quarter_end_month = 9
        else:
            quarter_end_month = 12

        # Начало квартала
        quarter_start_month = ((quarter_end_month - 1) // 3) * 3 + 1
        start = current_time.replace(
            month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # Конец квартала
        last_day = calendar.monthrange(year, quarter_end_month)[1]
        end = current_time.replace(
            month=quarter_end_month,
            day=last_day,
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )

        return start, end

    else:
        raise ValueError(f"Неизвестный тип прогноза: {prediction_type}")


def format_period_info(prediction_type: str, valid_until: datetime) -> str:
    """
    Форматирует информацию о периоде действия прогноза

    Args:
        prediction_type: Тип прогноза
        valid_until: Дата окончания действия прогноза

    Returns:
        str: Отформатированная строка с информацией о периоде
    """
    now = datetime.utcnow()
    time_left = valid_until - now

    if time_left.total_seconds() <= 0:
        return "⚠️ Прогноз истек"

    if prediction_type == "сегодня":
        if time_left.total_seconds() < 3600:  # Меньше часа
            minutes = int(time_left.total_seconds() // 60)
            return f"⏰ Действует еще {minutes} мин."
        else:
            hours = int(time_left.total_seconds() // 3600)
            return f"⏰ Действует еще {hours} ч."

    elif prediction_type == "неделя":
        days = time_left.days
        if days == 0:
            hours = int(time_left.total_seconds() // 3600)
            return f"⏰ Действует еще {hours} ч."
        else:
            return f"⏰ Действует еще {days} дн."

    elif prediction_type in ["месяц", "квартал"]:
        days = time_left.days
        if days == 0:
            hours = int(time_left.total_seconds() // 3600)
            return f"⏰ Действует еще {hours} ч."
        else:
            return f"⏰ Действует еще {days} дн."

    return ""


def get_next_available_time(
    prediction_type: str, current_time: datetime = None
) -> datetime:
    """
    Вычисляет время, когда можно будет запросить новый прогноз данного типа

    Args:
        prediction_type: Тип прогноза
        current_time: Текущее время

    Returns:
        datetime: Время следующего доступного запроса
    """
    if current_time is None:
        current_time = datetime.utcnow()

    _, period_end = get_prediction_period(prediction_type, current_time)

    # Следующий прогноз можно запросить через 1 секунду после окончания текущего периода
    return period_end + timedelta(seconds=1)
