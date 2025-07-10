import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from config import Config
from models import Location, PlanetPosition

logger = logging.getLogger(__name__)


def sanitize_html(text: str) -> str:
    """Удаляет неподдерживаемые HTML-теги для Telegram, оставляя только <b> и <i>."""
    
    # Удаляем markdown блоки кода с тройными кавычками
    text = re.sub(r'```[a-zA-Z]*\n?', '', text)  # Удаляем открывающие ```html или ```
    text = re.sub(r'```', '', text)              # Удаляем закрывающие ```
    
    # Удаляем другие markdown элементы
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)  # **bold** -> <b>bold</b>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)      # *italic* -> <i>italic</i>
    
    allowed = {"b", "i"}

    def replace_tag(match):
        tag_name = match.group(1).lower()
        if tag_name in allowed:
            return match.group(0)
        return ""

    # Удаляем неподдерживаемые HTML теги
    text = re.sub(r"</?([a-zA-Z0-9]+)[^>]*>", replace_tag, text)
    
    return text.strip()


class AIPredictionService:
    """Сервис AI-прогнозов"""

    def __init__(self):
        self.client = None

        logger.info("🔧 Инициализация AI сервиса прогнозов...")
        logger.info(f"OpenAI доступен: {OpenAI is not None}")
        logger.info(f"AI_API ключ: {'Установлен' if Config.AI_API else 'Отсутствует'}")

        if OpenAI and Config.AI_API:
            try:
                # Настройка клиента для работы с Bothub
                self.client = OpenAI(
                    api_key=Config.AI_API,
                    base_url="https://bothub.chat/api/v2/openai/v1",
                )
                logger.info("✅ AI клиент успешно создан")
                logger.info("✅ AI сервис прогнозов инициализирован")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации AI сервиса: {e}")
                self.client = None
        else:
            if not OpenAI:
                logger.error("❌ Библиотека OpenAI не установлена")
            if not Config.AI_API:
                logger.error("❌ AI_API ключ не найден в конфигурации")
            logger.warning("⚠️ AI клиент не будет создан, будут использоваться fallback прогнозы")

        # Инициализируем другие сервисы как None - создадим при необходимости
        self._aspect_calculator = None
        self._transit_calculator = None
        self._house_calculator = None

    @property
    def aspect_calculator(self):
        """Ленивая инициализация калькулятора аспектов"""
        if self._aspect_calculator is None:
            try:
                from .aspect_calculator import AspectCalculator
                self._aspect_calculator = AspectCalculator()
                logger.info("✅ AspectCalculator инициализирован")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации AspectCalculator: {e}")
                self._aspect_calculator = None
        return self._aspect_calculator

    @property
    def transit_calculator(self):
        """Ленивая инициализация калькулятора транзитов"""
        if self._transit_calculator is None:
            try:
                from .transit_calculator import TransitCalculator
                self._transit_calculator = TransitCalculator()
                logger.info("✅ TransitCalculator инициализирован")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации TransitCalculator: {e}")
                self._transit_calculator = None
        return self._transit_calculator

    @property
    def house_calculator(self):
        """Ленивая инициализация калькулятора домов"""
        if self._house_calculator is None:
            try:
                from .house_calculator import HouseCalculator
                self._house_calculator = HouseCalculator()
                logger.info("✅ HouseCalculator инициализирован")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации HouseCalculator: {e}")
                self._house_calculator = None
        return self._house_calculator

    def get_prediction_period(self, prediction_type: str) -> tuple[datetime, datetime]:
        """Возвращает период действия прогноза"""
        now = datetime.utcnow()

        if prediction_type == "сегодня":
            # Действует до конца дня
            valid_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            valid_until = valid_from + timedelta(days=1) - timedelta(seconds=1)
        elif prediction_type == "неделя":
            # Действует неделю с текущего момента
            valid_from = now
            valid_until = now + timedelta(days=7)
        elif prediction_type == "месяц":
            # Действует месяц с текущего момента
            valid_from = now
            if now.month == 12:
                valid_until = now.replace(year=now.year + 1, month=1)
            else:
                valid_until = now.replace(month=now.month + 1)
        elif prediction_type == "квартал":
            # Действует 3 месяца с текущего момента
            valid_from = now
            month = now.month
            year = now.year
            for _ in range(3):
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1
            valid_until = now.replace(year=year, month=month)
        else:
            # По умолчанию - день
            valid_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            valid_until = valid_from + timedelta(days=1) - timedelta(seconds=1)

        return valid_from, valid_until

    async def generate_prediction(
        self,
        user_planets: Dict[str, PlanetPosition],
        prediction_type: str = "общий",
        owner_name: str = None,
        birth_dt: datetime = None,
        location: Location = None,
    ) -> str:
        """Генерирует прогноз на основе натальной карты пользователя"""
        
        # Проверяем, включен ли AI в конфигурации
        if not Config.AI_ENABLED:
            logger.info("🔧 AI отключен в конфигурации, используем fallback")
            return self._generate_fallback_prediction(prediction_type, owner_name, "disabled")
        
        # Проверяем доступность AI клиента
        if not self.client:
            logger.warning("⚠️ AI клиент недоступен, используем fallback прогнозы")
            return self._generate_fallback_prediction(prediction_type, owner_name, "unavailable")
        
        try:
            # Определяем период действия прогноза
            valid_from, valid_until = self.get_prediction_period(prediction_type)
            
            # Формируем описание планетарных позиций
            planets_description = self._format_planets_for_ai(user_planets, birth_dt, location)
            
            # Формируем имя для AI
            name_for_ai = owner_name if owner_name and owner_name != "Ваша карта" else "пользователя"
            
            logger.info(f"🤖 Запрашиваем AI прогноз типа: {prediction_type} (таймаут: {Config.AI_REQUEST_TIMEOUT}с)")
            
            # Генерируем прогноз через AI с жестким таймаутом
            prediction = await self._generate_ai_prediction(
                prediction_type, name_for_ai, valid_from, valid_until, planets_description
            )
            
            if prediction:
                logger.info("✅ AI прогноз успешно сгенерирован")
                return prediction
            else:
                logger.warning("⚠️ AI вернул пустой прогноз, используем fallback")
                return self._generate_fallback_prediction(prediction_type, owner_name, "error")
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации AI прогноза: {e}")
            return self._generate_fallback_prediction(prediction_type, owner_name, "error")

    def _generate_fallback_prediction(self, prediction_type: str, owner_name: str = None, reason: str = "unavailable") -> str:
        """Генерирует резервный прогноз когда AI недоступен"""
        # Получаем период действия прогноза
        valid_from, valid_until = self.get_prediction_period(prediction_type)
        period_display = self._get_period_display(prediction_type, valid_from, valid_until)
        
        # Определяем заголовок
        if owner_name and owner_name != "Ваша карта":
            header = f"🔮 <b>Прогноз для {owner_name}</b>\n📅 {period_display}\n\n"
        else:
            header = f"🔮 <b>Ваш персональный прогноз</b>\n📅 {period_display}\n\n"
        
        # Выбираем текст в зависимости от типа прогноза
        predictions = {
            "сегодня": [
                "✨ <b>Сегодня звезды благосклонны к вам!</b>\n\n"
                "🌟 Утром ожидается прилив творческой энергии. Используйте это время для важных решений.\n\n"
                "💫 После обеда возможны интересные встречи или неожиданные возможности.\n\n"
                "🌙 Вечером уделите время себе и близким - это принесет гармонию.",
                
                "🌅 <b>День полон возможностей!</b>\n\n"
                "⭐ Первая половина дня благоприятна для начала новых дел.\n\n"
                "🔮 Интуиция будет особенно сильной - доверьтесь внутреннему голосу.\n\n"
                "🌺 К вечеру ожидается улучшение в личных отношениях."
            ],
            "неделя": [
                "🗓️ <b>Неделя принесет стабильность и рост!</b>\n\n"
                "📈 Первые дни недели - время для карьерных достижений.\n\n"
                "💝 Середина недели благоприятна для личных отношений.\n\n"
                "🎯 Выходные - идеальное время для планирования будущего.",
                
                "🌟 <b>Продуктивная неделя впереди!</b>\n\n"
                "💼 Рабочие вопросы будут решаться легко и быстро.\n\n"
                "❤️ В личной жизни ожидаются приятные сюрпризы.\n\n"
                "🌱 Новые идеи принесут долгожданные результаты."
            ],
            "месяц": [
                "📅 <b>Месяц трансформаций и роста!</b>\n\n"
                "🚀 Первая декада - время активных действий и новых проектов.\n\n"
                "⚖️ Вторая декада принесет баланс между работой и отдыхом.\n\n"
                "🏆 Третья декада - время сбора плодов ваших усилий.",
                
                "🌟 <b>Благоприятный период для всех сфер жизни!</b>\n\n"
                "💫 Финансовое положение будет укрепляться постепенно.\n\n"
                "👥 Отношения с окружающими выйдут на новый уровень.\n\n"
                "🎨 Творческие проекты получат неожиданное развитие."
            ]
        }
        
        # Получаем случайный прогноз для типа
        import random
        prediction_texts = predictions.get(prediction_type, predictions["сегодня"])
        prediction_text = random.choice(prediction_texts)
        
        # Добавляем сноску о режиме работы
        if reason == "timeout":
            footer = "\n\n<i>⚡ Прогноз создан в экспресс-режиме</i>"
        elif reason == "error":
            footer = "\n\n<i>🔧 Прогноз создан в автономном режиме</i>"
        elif reason == "disabled":
            footer = "\n\n<i>🛠️ AI временно отключен для стабильности</i>"
        else:
            footer = "\n\n<i>🌙 Прогноз основан на базовых астрологических принципах</i>"
        
        return header + prediction_text + footer

    def _get_period_display(
        self, prediction_type: str, valid_from: datetime, valid_until: datetime
    ) -> str:
        """Определяет отображение периода прогноза"""
        from_str = valid_from.strftime("%d.%m.%Y")
        until_str = valid_until.strftime("%d.%m.%Y")

        if prediction_type == "сегодня":
            return f"На {from_str}"
        elif prediction_type == "неделя":
            return f"На неделю: {from_str} - {until_str}"
        elif prediction_type == "месяц":
            return f"На месяц: {from_str} - {until_str}"
        elif prediction_type == "квартал":
            return f"На квартал: {from_str} - {until_str}"
        else:
            return f"На период: {from_str} - {until_str}"

    def _create_prediction_prompt(
        self,
        prediction_type: str,
        name_for_ai: str,
        valid_from: datetime,
        valid_until: datetime,
        planets_description: str,
    ) -> str:
        """Создает промпт в зависимости от типа прогноза"""
        from_str = valid_from.strftime("%d.%m.%Y")
        until_str = valid_until.strftime("%d.%m.%Y")

        base_instructions = """
Инструкции:
1. ОБЯЗАТЕЛЬНО учитывай аспекты между планетами - они ключевые для прогноза
2. Используй информацию о домах для понимания сфер жизни
3. Учитывай текущие транзиты планет
4. Обращай внимание на ретроградные планеты
5. Используй **только** HTML теги `<b>` для выделения. ЗАПРЕЩЕНО использовать любые другие HTML теги (например, `<h2>`, `<h3>`, `<p>`, `<div>`).
6. Прогноз должен быть 800-1000 символов
7. Структурируй по сферам с эмодзи-заголовками
8. Минимум воды, максимум конкретики
"""

        if prediction_type == "сегодня":
            return f"""Ты опытный астролог. Составь персональный астрологический прогноз для {name_for_ai} на день {from_str}.

{planets_description}

{base_instructions}

Обязательные разделы:
🌟 <b>Энергетика дня</b>
💼 <b>Работа и дела</b>
❤️ <b>Отношения</b>
💡 <b>Совет дня</b>

Фокус на практических советах основанных на аспектах и транзитах. 850-950 символов."""

        elif prediction_type == "неделя":
            return f"""Ты опытный астролог. Составь астрологический прогноз для {name_for_ai} на неделю ({from_str} - {until_str}).

{planets_description}

{base_instructions}

Обязательные разделы:
🔮 <b>Общие тенденции</b>
⭐ <b>Благоприятные дни</b>
⚠️ <b>Что избегать</b>
🎯 <b>Рекомендации</b>

Делай прогноз на основе взаимодействия натальных планет с текущими транзитами. 900-1000 символов."""

        elif prediction_type == "месяц":
            return f"""Ты опытный астролог. Составь детальный астрологический прогноз для {name_for_ai} на месяц ({from_str} - {until_str}).

{planets_description}

{base_instructions}

Обязательные разделы:
🌍 <b>Основные тенденции</b>
💰 <b>Карьера и финансы</b>
💕 <b>Личная жизнь</b>
📅 <b>Ключевые периоды</b>

Фокус на стратегических решениях основанных на долгосрочных транзитах. 950-1000 символов."""

        elif prediction_type == "квартал":
            return f"""Ты мастер-астролог. Составь стратегический астрологический прогноз для {name_for_ai} на квартал ({from_str} - {until_str}).

{planets_description}

{base_instructions}

Обязательные разделы:
🚀 <b>Долгосрочные тенденции</b>
🎯 <b>Ключевые возможности</b>
🛡️ <b>Вызовы и препятствия</b>
📋 <b>Стратегический план</b>

Создай глубокий анализ основанный на сложных астрологических взаимодействиях. 950-1000 символов."""

        else:
            return f"""Ты астролог. Создай персональный астрологический анализ для {name_for_ai}.

{planets_description}

Учитывай аспекты, дома, транзиты. 800-900 символов, структурированно, практично."""

    def _format_planets_for_ai(
        self,
        planets: Dict[str, PlanetPosition],
        birth_dt: datetime = None,
        location: Location = None,
    ) -> str:
        """Форматирует данные планет для отправки ИИ с расширенной астрологической информацией"""
        description_parts = []

        # Основные позиции планет
        description_parts.append("НАТАЛЬНАЯ КАРТА:")
        for planet_name, position in planets.items():
            degree_formatted = f"{position.degree:.1f}°"
            description_parts.append(
                f"• {planet_name} в {position.sign} ({degree_formatted})"
            )

        # ВРЕМЕННО ОТКЛЮЧАЕМ сложные вычисления для предотвращения зависания
        # Эти вычисления могут вызывать зависание при инициализации других сервисов
        logger.info("⚠️ Дополнительные астрологические вычисления временно отключены")

        return "\n".join(description_parts)

    async def _generate_ai_prediction(
        self,
        prediction_type: str,
        name_for_ai: str,
        valid_from: datetime,
        valid_until: datetime,
        planets_description: str,
    ) -> Optional[str]:
        """Генерирует прогноз через AI API с таймаутом и retry логикой"""
        
        import asyncio
        
        # Создаем промпт
        prompt = self._create_prediction_prompt(
            prediction_type, name_for_ai, valid_from, valid_until, planets_description
        )
        
        for attempt in range(Config.AI_MAX_RETRIES):
            try:
                logger.info(f"🤖 AI запрос попытка {attempt + 1}/{Config.AI_MAX_RETRIES}")
                
                # Выполняем запрос с таймаутом
                response = await asyncio.wait_for(
                    self._make_ai_request(prompt),
                    timeout=Config.AI_REQUEST_TIMEOUT
                )
                
                if response and response.strip():
                    # Очищаем ответ от неподдерживаемых HTML тегов
                    clean_response = sanitize_html(response.strip())
                    
                    # Добавляем период действия прогноза
                    period_display = self._get_period_display(prediction_type, valid_from, valid_until)
                    
                    if name_for_ai and name_for_ai != "пользователя":
                        header = f"🔮 <b>Прогноз для {name_for_ai}</b>\n📅 {period_display}\n\n"
                    else:
                        header = f"🔮 <b>Ваш персональный прогноз</b>\n📅 {period_display}\n\n"
                    
                    footer = "\n\n<i>✨ Создано с помощью астрологического ИИ</i>"
                    
                    return header + clean_response + footer
                    
            except asyncio.TimeoutError:
                logger.warning(f"⏰ AI запрос превысил таймаут {Config.AI_REQUEST_TIMEOUT}с (попытка {attempt + 1})")
                if attempt == Config.AI_MAX_RETRIES - 1:
                    logger.error("❌ Все попытки AI запроса истекли по таймауту")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Ошибка AI запроса (попытка {attempt + 1}): {e}")
                if attempt == Config.AI_MAX_RETRIES - 1:
                    logger.error("❌ Все попытки AI запроса завершились ошибками")
                    return None
                    
            # Небольшая пауза между попытками
            if attempt < Config.AI_MAX_RETRIES - 1:
                await asyncio.sleep(1)
        
        return None

    async def _make_ai_request(self, prompt: str) -> Optional[str]:
        """Выполняет асинхронный запрос к AI API через executor"""
        
        import asyncio
        import concurrent.futures
        
        def sync_request():
            """Синхронный запрос к AI"""
            try:
                logger.info(f"🔗 Отправляем запрос к AI API...")
                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=800,
                    timeout=25  # Максимальный таймаут для стабильности (30с - 5с на обработку)
                )
                
                if response.choices:
                    content = response.choices[0].message.content
                    logger.info(f"✅ Получен ответ от AI ({len(content) if content else 0} символов)")
                    return content
                else:
                    logger.warning("⚠️ AI ответ не содержит choices")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Ошибка синхронного AI запроса: {e}")
                return None
        
        try:
            # Выполняем в отдельном потоке
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, sync_request)
            return result
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка AI запроса: {e}")
            return None

    async def generate_compatibility_report(
        self,
        user_planets: Dict[str, PlanetPosition],
        partner_planets: Dict[str, PlanetPosition],
        sphere: str,
        user_name: str,
        partner_name: str,
    ) -> str:
        """Генерирует отчет о совместимости с помощью AI"""

        sphere_map = {
            "love": "любовных и романтических отношений",
            "career": "деловых и рабочих отношений",
            "friendship": "дружбы",
        }
        sphere_text = sphere_map.get(sphere, "взаимодействия")

        if not self.client:
            return "❌ Сервис совместимости временно недоступен."

        try:
            prompt = self._get_compatibility_prompt(
                user_planets, partner_planets, sphere_text, user_name, partner_name
            )

            # Используем асинхронный метод для AI запроса
            response = await self._make_ai_request(prompt)

            if response and response.strip():
                return sanitize_html(response.strip())
            else:
                return "❌ Не удалось получить анализ совместимости."

        except Exception as e:
            logger.error(f"Ошибка генерации отчета совместимости: {e}")
            return "❌ Произошла ошибка при создании анализа совместимости."

    def _get_compatibility_prompt(
        self, user_planets, partner_planets, sphere_text, user_name, partner_name
    ) -> str:
        """Создает промпт для анализа совместимости"""
        user_planets_str = self._format_planets_simple(user_planets)
        partner_planets_str = self._format_planets_simple(partner_planets)

        return f"""Ты опытный астролог-консультант. Проанализируй совместимость между {user_name} и {partner_name} в сфере {sphere_text}.

НАТАЛЬНАЯ КАРТА {user_name.upper()}:
{user_planets_str}

НАТАЛЬНАЯ КАРТА {partner_name.upper()}:
{partner_planets_str}

Создай подробный анализ совместимости (900-1000 символов), используя ТОЛЬКО HTML теги <b> для выделения.

СТРУКТУРА ОТВЕТА:

🌟 <b>Общая совместимость</b>
Проанализируй основные аспекты взаимодействия между партнерами. Как их Солнца, Луны и другие планеты влияют на отношения.

💫 <b>Сильные стороны</b>
Опиши конкретные аспекты и планетарные позиции, которые создают гармонию и взаимопонимание между партнерами.

⚠️ <b>Потенциальные сложности</b>
Укажи возможные конфликтные аспекты и различия в характерах, которые могут создавать напряжение.

💼 <b>В работе и делах</b>
Как партнеры взаимодействуют в профессиональной сфере, совместных проектах и деловых вопросах.

❤️ <b>В личных отношениях</b>
Эмоциональная совместимость, способность поддерживать друг друга, романтические аспекты.

🤝 <b>В дружбе и общении</b>
Как легко партнерам общаться, находить общие интересы, проводить время вместе.

💡 <b>Рекомендации</b>
Практические советы для улучшения отношений и использования сильных сторон совместимости.

ВАЖНО:
- НЕ используй численные оценки (типа "7 из 10")
- НЕ используй markdown форматирование (**, *, ```)
- НЕ используй блоки кода или тройные кавычки
- Используй ТОЛЬКО HTML теги <b> для выделения
- Основывайся на конкретных астрологических аспектах
- Пиши конкретно и по делу
- Каждый раздел 2-4 предложения"""

    def _format_planets_simple(self, planets: Dict[str, PlanetPosition]) -> str:
        """Упрощенное форматирование планет для AI запросов"""
        result = []
        for planet, position in planets.items():
            result.append(f"{planet}: {position.sign} {position.degree:.0f}°")
        return ", ".join(result) 