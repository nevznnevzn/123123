import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class UserLimits:
    """Лимиты пользователя"""

    daily_questions: int
    cooldown_minutes: int
    is_premium: bool = False


@dataclass
class UserStats:
    """Статистика использования пользователем"""

    questions_today: int = 0
    last_question_time: Optional[datetime] = None
    daily_reset_date: Optional[datetime] = None


class AntiSpamService:
    """Сервис антиспама для ограничения AI-запросов"""

    # Лимиты для разных типов пользователей
    FREE_LIMITS = UserLimits(daily_questions=3, cooldown_minutes=3, is_premium=False)

    PREMIUM_LIMITS = UserLimits(
        daily_questions=999,  # Практически без лимитов
        cooldown_minutes=1,  # Минимальный кулдаун
        is_premium=True,
    )

    def __init__(self):
        # В памяти храним статистику (в продакшене лучше в Redis или БД)
        self._user_stats: Dict[int, UserStats] = {}

    def get_user_limits(self, user_id: int, is_premium: bool = False) -> UserLimits:
        """Получает лимиты для пользователя"""
        return self.PREMIUM_LIMITS if is_premium else self.FREE_LIMITS

    def get_user_stats(self, user_id: int) -> UserStats:
        """Получает статистику пользователя"""
        if user_id not in self._user_stats:
            self._user_stats[user_id] = UserStats()

        stats = self._user_stats[user_id]

        # Сброс счетчика в новый день
        now = datetime.now()
        if (
            stats.daily_reset_date is None
            or stats.daily_reset_date.date() != now.date()
        ):
            stats.questions_today = 0
            stats.daily_reset_date = now

        return stats

    def check_limits(self, user_id: int, is_premium: bool = False) -> Dict[str, any]:
        """
        Проверяет ограничения для пользователя

        Returns:
            {
                "allowed": bool,
                "reason": str,
                "wait_time": Optional[timedelta],
                "questions_left": int
            }
        """
        limits = self.get_user_limits(user_id, is_premium)
        stats = self.get_user_stats(user_id)
        now = datetime.now()

        # Проверяем дневной лимит
        if stats.questions_today >= limits.daily_questions:
            return {
                "allowed": False,
                "reason": "daily_limit",
                "wait_time": None,
                "questions_left": 0,
                "limit_type": "Дневной лимит исчерпан",
            }

        # Проверяем кулдаун
        if stats.last_question_time:
            time_since_last = now - stats.last_question_time
            cooldown_required = timedelta(minutes=limits.cooldown_minutes)

            if time_since_last < cooldown_required:
                wait_time = cooldown_required - time_since_last
                return {
                    "allowed": False,
                    "reason": "cooldown",
                    "wait_time": wait_time,
                    "questions_left": limits.daily_questions - stats.questions_today,
                    "limit_type": "Кулдаун активен",
                }

        # Все проверки пройдены
        questions_left = limits.daily_questions - stats.questions_today
        return {
            "allowed": True,
            "reason": "ok",
            "wait_time": None,
            "questions_left": questions_left
            - 1,  # -1 потому что этот запрос будет засчитан
            "limit_type": None,
        }

    def record_question(self, user_id: int):
        """Записывает факт задания вопроса"""
        stats = self.get_user_stats(user_id)
        stats.questions_today += 1
        stats.last_question_time = datetime.now()

        logger.info(
            f"Пользователь {user_id} задал вопрос. Всего сегодня: {stats.questions_today}"
        )

    def get_stats_text(self, user_id: int, is_premium: bool = False) -> str:
        """Возвращает текстовую информацию о лимитах пользователя"""
        limits = self.get_user_limits(user_id, is_premium)
        stats = self.get_user_stats(user_id)

        if is_premium:
            return "💎 <b>Premium статус</b> - практически без ограничений!"

        questions_left = limits.daily_questions - stats.questions_today

        text = f"📊 <b>Ваши лимиты:</b>\n"
        text += (
            f"• Вопросов сегодня: {stats.questions_today}/{limits.daily_questions}\n"
        )
        text += f"• Осталось вопросов: {questions_left}\n"
        text += f"• Кулдаун между вопросами: {limits.cooldown_minutes} мин\n\n"

        if questions_left <= 1:
            text += "💡 <b>Совет:</b> Получите Premium для снятия ограничений!"

        return text

    def format_wait_time(self, wait_time: timedelta) -> str:
        """Форматирует время ожидания в читаемый вид"""
        total_seconds = int(wait_time.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        if minutes > 0:
            return f"{minutes} мин {seconds} сек"
        else:
            return f"{seconds} сек"

    def reset_user_stats(self, user_id: int):
        """Сбрасывает статистику пользователя (для админа)"""
        if user_id in self._user_stats:
            del self._user_stats[user_id]
        logger.info(f"Статистика пользователя {user_id} сброшена")
