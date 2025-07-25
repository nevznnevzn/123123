import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from models import Location, PlanetPosition

from .ai_predictions import AIPredictionService

logger = logging.getLogger(__name__)


class StarAdviceService:
    """Сервис Звёздного совета - астрологический AI-консультант"""

    # Категории вопросов и их астрологические приоритеты
    CATEGORY_PRIORITIES = {
        "career": {
            "planets": ["Солнце", "Марс", "Юпитер", "Сатурн"],
            "houses": [10, 6, 2],
            "transits": ["Сатурн", "Юпитер"],
            "description": "карьеры и профессиональной деятельности",
        },
        "love": {
            "planets": ["Венера", "Луна", "Марс", "Солнце"],
            "houses": [7, 5, 8],
            "transits": ["Венера", "Марс"],
            "description": "отношений и любви",
        },
        "finances": {
            "planets": ["Венера", "Юпитер", "Сатурн"],
            "houses": [2, 8, 11],
            "transits": ["Юпитер", "Сатурн"],
            "description": "финансов и материальных ресурсов",
        },
        "family": {
            "planets": ["Луна", "Венера", "Солнце"],
            "houses": [4, 3, 10],
            "transits": ["Луна", "Венера"],
            "description": "семьи и домашних дел",
        },
        "growth": {
            "planets": ["Солнце", "Юпитер", "Уран", "Нептун"],
            "houses": [9, 12, 1],
            "transits": ["Юпитер", "Уран", "Нептун"],
            "description": "личностного роста и духовного развития",
        },
        "other": {
            "planets": ["Солнце", "Луна", "Асцендент"],
            "houses": [1, 7, 10],
            "transits": ["Юпитер", "Сатурн"],
            "description": "общих жизненных вопросов",
        },
    }

    # Ключевые слова для отклонения неастрологических вопросов
    FORBIDDEN_KEYWORDS = [
        # Технологии и ИИ
        "модель",
        "gpt",
        "chatgpt",
        "искусственный интеллект",
        "ai",
        "ии",
        "программа",
        "код",
        "разработка",
        "алгоритм",
        "нейросет",
        # Медицина и здоровье (точные диагнозы)
        "диагноз",
        "лечение",
        "болезнь",
        "препарат",
        "таблетк",
        "врач",
        "медицин",
        "больниц",
        "операци",
        "симптом",
        # Другие неастрологические темы
        "погода",
        "курс валют",
        "новости",
        "политика",
        "выборы",
        "рецепт",
        "готов",
        "кулинар",
        "спорт",
        "футбол",
        "хоккей",
    ]

    # Астрологические ключевые слова (хотя бы одно должно присутствовать)
    ASTRO_KEYWORDS = [
        "планет",
        "знак",
        "гороскоп",
        "астрология",
        "астролог",
        "транзит",
        "ретроград",
        "натальн",
        "карт",
        "аспект",
        "дом",
        "солнце",
        "луна",
        "венера",
        "марс",
        "отношени",
        "карьер",
        "любов",
        "совет",
        "прогноз",
        "судьба",
        "характер",
        "личность",
        "партнер",
        "работа",
        "деньги",
        "семья",
        "будущее",
        # Новые ключевые слова для работы и задач
        "задач",
        "проект",
        "офис",
        "коллег",
        "профессионал",
        "трудность",
        "карьерный",
        "должность",
        "руководител",
        "команда",
        "босс",
        "начальник",
        "подчинённ",
        "развитие",
        "успех",
        "достижение",
        "цель",
        "мотивация",
        "продуктивност",
        "выгорание",
        "конфликт",
        "повышение",
        "поиск работы",
        "смена работы",
        "увольнение",
        "работодатель",
        "резюме",
        "собеседование",
        "карьерный рост",
    ]

    def __init__(self):
        self.ai_service = AIPredictionService()

    async def validate_question(self, question: str) -> Dict[str, any]:
        """
        Проверяет, подходит ли вопрос для астрологической консультации

        Returns:
            {"is_valid": bool, "reason": str}
        """
        question_lower = question.lower()

        # Логирование для отладки фильтрации
        logger.info(f"[StarAdvice] Проверка вопроса на запрещённые слова: '{question_lower}'")

        # Проверка на запрещенные ключевые слова
        for forbidden in self.FORBIDDEN_KEYWORDS:
            if forbidden in question_lower:
                logger.warning(f"[StarAdvice] Найдено запрещённое слово: '{forbidden}' в вопросе: '{question_lower}'")
                return {
                    "is_valid": False,
                    "reason": f"Вопрос содержит неастрологическую тематику: '{forbidden}'",
                }

        # Проверка минимальной длины
        if len(question.strip()) < 10:
            return {
                "is_valid": False,
                "reason": "Вопрос слишком короткий. Опишите ситуацию подробнее.",
            }

        if len(question.strip()) > 500:
            return {
                "is_valid": False,
                "reason": "Вопрос слишком длинный. Максимум 500 символов.",
            }

        # Проверка на наличие астрологических ключевых слов
        has_astro_keywords = any(
            keyword in question_lower for keyword in self.ASTRO_KEYWORDS
        )

        # Если нет астрологических слов, проверяем через AI
        if not has_astro_keywords:
            ai_validation = await self._ai_validate_question(question)
            if not ai_validation["is_valid"]:
                return ai_validation

        return {"is_valid": True, "reason": ""}

    async def _ai_validate_question(self, question: str) -> Dict[str, any]:
        """AI-валидация вопроса для фильтрации неподходящих запросов"""

        if not self.ai_service.client:
            logger.warning("AI клиент недоступен для валидации")
            return {"is_valid": True, "reason": ""}  # Пропускаем без AI

        try:
            validation_prompt = f"""
            Оцени, подходит ли этот вопрос для астрологической консультации:
            "{question}"

            НЕ ПРИНИМАЕМ:
            - Технические вопросы об ИИ, программировании, технологиях
            - Медицинские диагнозы и лечение
            - Прогнозы погоды, курсов валют, новостей
            - Кулинарные рецепты
            - Спортивные результаты
            - Политические вопросы
            - Просьбы написать код или программы

            ПРИНИМАЕМ:
            - Вопросы о личности, характере, поведении
            - Отношения, любовь, семья
            - Карьера, работа, финансы
            - Жизненные ситуации требующие мудрого совета
            - Вопросы о будущем, выборе, решениях
            - Астрологические темы
            - ВОПРОСЫ О РАБОТЕ, ЗАДАЧАХ, ПРОЕКТАХ, ОФИСЕ, КОЛЛЕГАХ, ПРОФЕССИОНАЛЬНЫХ ТРУДНОСТЯХ, КАРЬЕРНЫХ ЦЕЛЯХ — ВСЕГДА ПРИНИМАЕМ

            Ответь ТОЛЬКО одним словом: "ПРИНЯТ" или "ОТКЛОНЕН"
            """

            # Выполняем AI запрос асинхронно
            result_text = await self._make_async_ai_request_validation(validation_prompt)
            
            if not result_text:
                # Если AI недоступен, пропускаем валидацию
                logger.warning("AI валидация недоступна, пропускаем проверку")
                return {"is_valid": True, "reason": ""}

            result = result_text.strip().upper()

            if "ПРИНЯТ" in result:
                return {"is_valid": True, "reason": ""}
            else:
                return {
                    "is_valid": False,
                    "reason": "Этот вопрос не подходит для астрологической консультации. Попробуйте спросить о жизненной ситуации, отношениях, карьере или личностных вопросах.",
                }

        except Exception as e:
            logger.error(f"Ошибка AI-валидации вопроса: {e}")
            # В случае ошибки AI, не пропускаем, а сообщаем о проблеме
            return {
                "is_valid": False,
                "reason": "Не удалось проверить ваш вопрос с помощью AI-ассистента. Возможно, проблема с API. Попробуйте позже.",
            }

    async def _make_async_ai_request_validation(self, prompt: str) -> str:
        """Выполняет асинхронный запрос к AI API для валидации"""
        import asyncio
        
        def sync_validation_request():
            """Синхронный AI запрос для валидации"""
            try:
                response = self.ai_service.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=10,
                    timeout=10  # Короткий таймаут для валидации
                )
                
                if response.choices:
                    return response.choices[0].message.content
                return None
                
            except Exception as e:
                logger.error(f"Ошибка AI валидации: {e}")
                return None
        
        try:
            # Выполняем в отдельном потоке с коротким таймаутом
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, sync_validation_request),
                timeout=15  # Общий таймаут 15 секунд для валидации
            )
            return result
            
        except asyncio.TimeoutError:
            logger.error("AI валидация превысила таймаут")
            return None
        except Exception as e:
            logger.error(f"Критическая ошибка AI валидации: {e}")
            return None

    async def generate_advice(
        self,
        question: str,
        category: str,
        user_planets: Dict[str, PlanetPosition],
        birth_dt: datetime,
        location: Location,
        user_name: str = "пользователь",
    ) -> str:
        """Генерирует астрологический совет на основе вопроса и натальной карты"""

        if not self.ai_service.client:
            return "❌ Сервис советов временно недоступен. Проверьте настройки API."

        try:
            # Получаем приоритеты для категории
            priorities = self.CATEGORY_PRIORITIES.get(
                category, self.CATEGORY_PRIORITIES["other"]
            )

            # Формируем контекст для AI
            astro_context = await self._build_astro_context_async(
                user_planets, birth_dt, location, priorities
            )

            # Создаем промпт
            prompt = self._create_advice_prompt(
                question, category, astro_context, user_name, priorities
            )

            # Получаем ответ от AI АСИНХРОННО
            response = await self._make_async_ai_request(prompt)
            
            if not response:
                return "❌ Не удалось получить ответ от AI. Попробуйте позже."

            advice = response

            # Добавляем заголовок
            category_desc = priorities["description"]
            header = f"🌟 <b>Звёздный совет по вопросам {category_desc}</b>\n\n"

            result = f"{header}{advice}"

            # Проверяем длину и обрезаем если нужно
            if len(result) > 3000:
                available_length = 3000 - len(header) - 10
                # Обрезаем по последнему полному предложению
                truncated_advice = advice[:available_length]
                last_sentence = truncated_advice.rfind('.')
                if last_sentence > available_length // 2:  # Если есть точка в разумном месте
                    advice = truncated_advice[:last_sentence + 1] + "\n\n<i>...</i>"
                else:
                    advice = truncated_advice + "..."
                result = f"{header}{advice}"

            return result

        except Exception as e:
            logger.error(f"Ошибка генерации совета: {e}")
            return "❌ Произошла ошибка при генерации совета. Пожалуйста, попробуйте позже."

    async def _make_async_ai_request(self, prompt: str) -> str:
        """Выполняет асинхронный запрос к AI API"""
        import asyncio
        import concurrent.futures
        
        def sync_ai_request():
            """Синхронный AI запрос для выполнения в executor"""
            try:
                response = self.ai_service.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=400,
                    timeout=20  # Таймаут 20 секунд
                )
                
                if response.choices:
                    return response.choices[0].message.content
                return None
                
            except Exception as e:
                logger.error(f"Ошибка AI запроса: {e}")
                return None
        
        try:
            # Выполняем в отдельном потоке с таймаутом
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, sync_ai_request),
                timeout=25  # Общий таймаут 25 секунд
            )
            return result
            
        except asyncio.TimeoutError:
            logger.error("AI запрос превысил таймаут")
            return None
        except Exception as e:
            logger.error(f"Критическая ошибка AI запроса: {e}")
            return None

    async def _build_astro_context_async(
        self,
        planets: Dict[str, PlanetPosition],
        birth_dt: datetime,
        location: Location,
        priorities: Dict,
    ) -> str:
        """Асинхронно формирует астрологический контекст для AI"""
        context_parts = []

        # Приоритетные планеты для данной категории
        context_parts.append("КЛЮЧЕВЫЕ ПЛАНЕТЫ:")
        for planet_name in priorities["planets"]:
            if planet_name in planets:
                position = planets[planet_name]
                context_parts.append(
                    f"• {planet_name} в {position.sign} ({position.degree:.1f}°)"
                )

        # Все остальные планеты (кратко)
        context_parts.append("\nОСТАЛЬНЫЕ ПЛАНЕТЫ:")
        for planet_name, position in planets.items():
            if planet_name not in priorities["planets"]:
                context_parts.append(f"• {planet_name}: {position.sign}")

        # Добавляем аспекты АСИНХРОННО (если есть и сервис инициализирован)
        if (hasattr(self.ai_service, "aspect_calculator") and 
            self.ai_service.aspect_calculator is not None):
            try:
                # Выполняем в executor чтобы не блокировать event loop
                import asyncio
                loop = asyncio.get_event_loop()
                aspects = await asyncio.wait_for(
                    loop.run_in_executor(
                        None, 
                        lambda: self.ai_service.aspect_calculator.get_major_aspects(
                            planets, max_count=5
                        )
                    ),
                    timeout=5  # Таймаут 5 секунд на аспекты
                )
                if aspects:
                    context_parts.append("\nКЛЮЧЕВЫЕ АСПЕКТЫ:")
                    for aspect in aspects:
                        context_parts.append(f"• {aspect}")
            except asyncio.TimeoutError:
                logger.warning("Расчет аспектов превысил таймаут, пропускаем")
            except Exception as e:
                logger.warning(f"Не удалось получить аспекты: {e}")

        # Добавляем транзиты АСИНХРОННО (если есть и сервис инициализирован)
        if (hasattr(self.ai_service, "transit_calculator") and 
            self.ai_service.transit_calculator is not None):
            try:
                # Выполняем в executor чтобы не блокировать event loop
                import asyncio
                loop = asyncio.get_event_loop()
                transits = await asyncio.wait_for(
                    loop.run_in_executor(
                        None, 
                        lambda: self.ai_service.transit_calculator.get_current_transits(
                            birth_dt, location
                        )
                    ),
                    timeout=10  # Таймаут 10 секунд на транзиты
                )
                if transits:
                    context_parts.append("\nТЕКУЩИЕ ТРАНЗИТЫ:")
                    for transit in transits[:3]:  # Только самые важные
                        context_parts.append(f"• {transit}")
            except asyncio.TimeoutError:
                logger.warning("Расчет транзитов превысил таймаут, пропускаем")
            except Exception as e:
                logger.warning(f"Не удалось получить транзиты: {e}")

        return "\n".join(context_parts)

    def _create_advice_prompt(
        self,
        question: str,
        category: str,
        astro_context: str,
        user_name: str,
        priorities: Dict,
    ) -> str:
        """Создает промпт для генерации совета"""

        category_desc = priorities["description"]

        prompt = f"""
        Ты мудрый и опытный астролог-консультант. Пользователь обращается к тебе за советом по вопросам {category_desc}.
        
        НАТАЛЬНАЯ КАРТА ПОЛЬЗОВАТЕЛЯ:
        {astro_context}
        
        ВОПРОС ОТ {user_name.upper()}:
        "{question}"
        
        ИНСТРУКЦИИ:
        1. Дай мудрый, практичный совет, основанный на астрологических факторах
        2. Используй информацию из натальной карты и текущих транзитов
        3. Будь эмпатичным, поддерживающим, но честным
        4. Структурируй ответ с HTML-тегами <b> для выделения
        5. Максимум 350 слов
        6. Избегай категоричных предсказаний, давай рекомендации
        
        СТРУКТУРА ОТВЕТА:
        🔮 <b>Астрологический анализ ситуации</b>
        [2-3 предложения об астрологических факторах]
        
        💫 <b>Мой совет</b>
        [Конкретные практические рекомендации]
        
        ⭐ <b>На что обратить внимание</b>
        [Важные моменты для учета]
        
        Говори тепло, как мудрый наставник, который искренне хочет помочь.
        """

        return prompt
