import logging
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from database import DatabaseManager, User, db_manager
from services.ai_predictions import AIPredictionService
from services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


class MotivationService:
    """
    Сервис для генерации ежедневных мотивационных сообщений.
    """

    def __init__(self, ai_service: AIPredictionService):
        self.ai_service = ai_service
        self.subscription_service = SubscriptionService()

    async def generate_motivation(
        self, user: User, is_subscribed: bool = None
    ) -> Optional[str]:
        """
        Генерирует мотивационное сообщение для пользователя.

        :param user: Объект пользователя.
        :param is_subscribed: Является ли пользователь подписчиком (автоопределение если None).
        :return: Текст мотивации или None в случае ошибки.
        """
        logger.info(f"Генерация мотивации для пользователя {user.telegram_id}")

        # Определяем статус подписки если не передан
        if is_subscribed is None:
            is_subscribed = self.subscription_service.is_user_premium(user.telegram_id)

        try:
            # Получаем натальную карту пользователя
            user_charts = db_manager.get_user_charts(user.telegram_id)
            if not user_charts:
                logger.warning(
                    f"У пользователя {user.telegram_id} нет натальных карт для генерации мотивации."
                )
                return await self._generate_generic_motivation(user.name, is_subscribed)

            # Берем первую (основную) карту
            natal_chart = user_charts[0]
            planets_data = natal_chart.get_planets_data()

            if not planets_data:
                logger.warning(
                    f"Натальная карта пользователя {user.telegram_id} не содержит данных о планетах."
                )
                return await self._generate_generic_motivation(user.name, is_subscribed)

            # Фильтруем планеты в зависимости от подписки
            filtered_planets = self.subscription_service.filter_planets_for_user(
                planets_data, user.telegram_id
            )

            # Формируем детальный промпт на основе натальной карты
            prompt = self._create_astro_prompt(
                user_name=user.name,
                planets=filtered_planets,
                birth_date=natal_chart.birth_date,
                is_subscribed=is_subscribed,
            )

            # Генерируем мотивацию через AI
            motivation_text = await self.ai_service.get_chat_completion(
                prompt=prompt, messages_history=[]
            )

            # Добавляем призыв к подписке для бесплатных пользователей
            if not is_subscribed:
                motivation_text += "\n\n✨ *Хотите получать полный астрологический прогноз с учетом всех планет? Оформите Premium подписку!*"

            return motivation_text

        except Exception as e:
            logger.error(f"Ошибка при генерации мотивации для {user.telegram_id}: {e}")
            # В случае ошибки возвращаем общую мотивацию
            return await self._generate_generic_motivation(user.name, is_subscribed)

    async def _generate_generic_motivation(
        self, user_name: str, is_subscribed: bool
    ) -> Optional[str]:
        """Генерирует общую мотивацию без учета натальной карты"""
        try:
            if is_subscribed:
                prompt = f"Создай полную, вдохновляющую мотивацию на сегодняшний день для пользователя {user_name}. Сделай её персональной и позитивной."
            else:
                prompt = f"Создай короткую, мотивирующую цитату на день для пользователя {user_name}. Максимум 2-3 предложения."

            motivation_text = await self.ai_service.get_chat_completion(
                prompt=prompt, messages_history=[]
            )

            if not is_subscribed:
                motivation_text += "\n\n✨ *Хотите получать персональные астрологические прогнозы? Оформите Premium подписку!*"

            return motivation_text

        except Exception as e:
            logger.error(f"Ошибка при генерации общей мотивации: {e}")
            return None

    def _create_astro_prompt(
        self, user_name: str, planets: dict, birth_date, is_subscribed: bool
    ) -> str:
        """
        Создает астрологический промпт на основе натальной карты пользователя.
        """
        # Формируем описание планет
        planets_description = []
        for planet_name, position in planets.items():
            planets_description.append(
                f"{planet_name} в {position.sign} {position.degree:.1f}°"
            )

        planets_text = ", ".join(planets_description)

        # Определяем длину и детальность прогноза
        if is_subscribed:
            detail_level = "детальную астрологическую мотивацию с учетом текущих транзитов и аспектов"
            length = "3-4 абзаца"
        else:
            detail_level = "краткую астрологическую мотивацию"
            length = "2-3 предложения"

        prompt = f"""
Создай {detail_level} на сегодняшний день для пользователя {user_name}.

Натальная карта:
{planets_text}

Учти влияние этих планетарных позиций на характер и потенциал человека. 
Создай вдохновляющее сообщение длиной {length}, которое:
1. Подчеркивает сильные стороны на основе планетарных позиций
2. Дает практические советы на день
3. Мотивирует к действию

Пиши тепло, персонально и позитивно. Начни с обращения к пользователю по имени.
"""
        return prompt.strip()

    def _create_prompt(self, natal_chart, is_subscribed: bool) -> str:
        """
        Устаревший метод - оставлен для совместимости.
        Используй _create_astro_prompt вместо этого.
        """
        logger.warning("Используется устаревший метод _create_prompt")
        return "Общая мотивация на день."


async def send_daily_motivation(bot: Bot, db_manager: DatabaseManager):
    """
    Выполняет ежедневную рассылку мотивационных сообщений.
    """
    logger.info("🚀 Запуск ежедневной рассылки мотиваций...")

    ai_service = AIPredictionService()
    motivation_service = MotivationService(ai_service=ai_service)

    users_for_mailing = db_manager.get_users_for_mailing()

    sent_count = 0
    failed_count = 0

    for user in users_for_mailing:
        try:
            is_premium = user.is_premium
            motivation_text = await motivation_service.generate_motivation(
                user, is_subscribed=is_premium
            )

            if motivation_text:
                await bot.send_message(user.telegram_id, motivation_text)
                sent_count += 1
                logger.info(f"✅ Мотивация отправлена пользователю {user.telegram_id}")
            else:
                logger.warning(
                    f"Не удалось сгенерировать мотивацию для пользователя {user.telegram_id}"
                )
                failed_count += 1

        except TelegramAPIError as e:
            logger.error(
                f"❌ Ошибка отправки сообщения пользователю {user.telegram_id}: {e}"
            )
            failed_count += 1
        except Exception as e:
            logger.error(
                f"❌ Непредвиденная ошибка при обработке пользователя {user.telegram_id}: {e}"
            )
            failed_count += 1

    logger.info(
        f"✅ Рассылка завершена. Отправлено: {sent_count}, Ошибок: {failed_count}"
    )


# Пример того, как это будет инициализироваться в main.py
# ai_prediction_service = AIPredictionService()
# motivation_service = MotivationService(ai_service=ai_prediction_service)
