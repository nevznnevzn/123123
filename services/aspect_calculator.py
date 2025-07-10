import logging
from itertools import combinations
from typing import Dict, List, Optional, Tuple

from config import Config
from models import PlanetPosition

logger = logging.getLogger(__name__)


class AspectCalculator:
    """Калькулятор для определения астрологических аспектов между планетами."""

    # Основные аспекты и их углы (в градусах)
    ASPECTS = {
        "Соединение": {
            "angle": 0,
            "base_orb": 8,
            "type": "major",
            "symbol": "☌",
            "nature": "neutral",
        },
        "Оппозиция": {
            "angle": 180,
            "base_orb": 8,
            "type": "major",
            "symbol": "☍",
            "nature": "hard",
        },
        "Трин": {
            "angle": 120,
            "base_orb": 7,
            "type": "major",
            "symbol": "△",
            "nature": "soft",
        },
        "Квадрат": {
            "angle": 90,
            "base_orb": 7,
            "type": "major",
            "symbol": "□",
            "nature": "hard",
        },
        "Секстиль": {
            "angle": 60,
            "base_orb": 5,
            "type": "major",
            "symbol": "⚹",
            "nature": "soft",
        },
        "Квиконс": {
            "angle": 150,
            "base_orb": 3,
            "type": "minor",
            "symbol": "⚻",
            "nature": "hard",
        },
        "Полусекстиль": {
            "angle": 30,
            "base_orb": 2,
            "type": "minor",
            "symbol": "⚺",
            "nature": "soft",
        },
        "Полуквадрат": {
            "angle": 45,
            "base_orb": 2,
            "type": "minor",
            "symbol": "∠",
            "nature": "hard",
        },
        "Полутораквадрат": {
            "angle": 135,
            "base_orb": 2,
            "type": "minor",
            "symbol": "⚼",
            "nature": "hard",
        },
    }

    # Множители орбов для разных планет (чем важнее планета, тем больше орб)
    PLANET_ORB_MULTIPLIERS = {
        "Солнце": 1.2,  # Светила получают больший орб
        "Луна": 1.2,
        "Меркурий": 1.0,  # Личные планеты - стандартный орб
        "Венера": 1.0,
        "Марс": 1.0,
        "Юпитер": 0.9,  # Социальные планеты - чуть меньший орб
        "Сатурн": 0.9,
        "Уран": 0.8,  # Высшие планеты - меньший орб
        "Нептун": 0.8,
        "Плутон": 0.8,
    }

    def _get_planet_orb_multiplier(self, planet1: str, planet2: str) -> float:
        """Получает множитель орба для пары планет (берется максимальный)"""
        mult1 = self.PLANET_ORB_MULTIPLIERS.get(planet1, 0.8)
        mult2 = self.PLANET_ORB_MULTIPLIERS.get(planet2, 0.8)
        return max(mult1, mult2)

    def _calculate_orb_for_planets(
        self, aspect_name: str, planet1: str, planet2: str
    ) -> float:
        """Рассчитывает орб для конкретной пары планет"""
        base_orb = self.ASPECTS[aspect_name]["base_orb"]
        multiplier = self._get_planet_orb_multiplier(planet1, planet2)
        return base_orb * multiplier

    def _sign_to_degrees(self, sign: str) -> float:
        """Конвертирует знак зодиака в градусы от 0° Овна."""
        try:
            sign_index = Config.ZODIAC_SIGNS.index(sign)
            return sign_index * 30
        except (ValueError, IndexError):
            logger.warning(f"Неизвестный знак зодиака: {sign}")
            return 0

    def _normalize_angle(self, angle: float) -> float:
        """Нормализует угол к диапазону 0-360°"""
        while angle < 0:
            angle += 360
        while angle >= 360:
            angle -= 360
        return angle

    def _calculate_angular_distance(self, pos1: float, pos2: float) -> float:
        """Рассчитывает угловое расстояние между двумя позициями"""
        diff = abs(pos1 - pos2)
        return min(diff, 360 - diff)

    def _calculate_aspect_strength(self, orb: float, max_orb: float) -> float:
        """Рассчитывает силу аспекта (0-100%, где 100% = точный аспект)"""
        if orb > max_orb:
            return 0.0
        return ((max_orb - orb) / max_orb) * 100

    def get_major_aspects(
        self, planets: Dict[str, PlanetPosition], max_count: int = 5
    ) -> List[str]:
        """
        Находит и форматирует основные (мажорные) аспекты между планетами.

        Args:
            planets: Словарь с позициями планет.
            max_count: Максимальное количество аспектов для возврата.

        Returns:
            Список отформатированных мажорных аспектов.
        """
        all_aspects = self._calculate_all_aspects(planets)
        major_aspects = [
            aspect
            for aspect in all_aspects
            if self.ASPECTS[aspect["name"]]["type"] == "major"
        ]

        # Сортируем по силе аспекта (сначала более точные)
        major_aspects.sort(key=lambda x: x["strength"], reverse=True)

        # Форматируем и возвращаем
        formatted_aspects = [self._format_aspect(aspect) for aspect in major_aspects]
        return formatted_aspects[:max_count]

    def get_all_aspects(
        self, planets: Dict[str, PlanetPosition], include_minor: bool = False
    ) -> List[Dict]:
        """
        Получает все аспекты с подробной информацией.

        Args:
            planets: Словарь с позициями планет
            include_minor: Включать ли минорные аспекты

        Returns:
            Список аспектов с подробной информацией
        """
        all_aspects = self._calculate_all_aspects(planets)

        if not include_minor:
            all_aspects = [
                aspect
                for aspect in all_aspects
                if self.ASPECTS[aspect["name"]]["type"] == "major"
            ]

        # Сортируем по силе
        all_aspects.sort(key=lambda x: x["strength"], reverse=True)
        return all_aspects

    def _calculate_all_aspects(self, planets: Dict[str, PlanetPosition]) -> List[Dict]:
        """Рассчитывает все аспекты между всеми планетами."""
        aspect_list = []
        planet_names = list(planets.keys())

        # Создаем все возможные пары планет
        for p1_name, p2_name in combinations(planet_names, 2):
            p1_pos = planets[p1_name]
            p2_pos = planets[p2_name]

            # Конвертируем позиции в абсолютные градусы
            p1_abs_degree = self._sign_to_degrees(p1_pos.sign) + p1_pos.degree
            p2_abs_degree = self._sign_to_degrees(p2_pos.sign) + p2_pos.degree

            # Вычисляем угловое расстояние
            angle_diff = self._calculate_angular_distance(p1_abs_degree, p2_abs_degree)

            # Проверяем на наличие аспектов
            for aspect_name, aspect_info in self.ASPECTS.items():
                target_angle = aspect_info["angle"]
                orb_deviation = abs(angle_diff - target_angle)

                # Рассчитываем орб для данной пары планет
                max_orb = self._calculate_orb_for_planets(aspect_name, p1_name, p2_name)

                if orb_deviation <= max_orb:
                    strength = self._calculate_aspect_strength(orb_deviation, max_orb)

                    aspect_list.append(
                        {
                            "p1": p1_name,
                            "p2": p2_name,
                            "name": aspect_name,
                            "orb": orb_deviation,
                            "max_orb": max_orb,
                            "strength": strength,
                            "nature": aspect_info["nature"],
                            "type": aspect_info["type"],
                            "symbol": aspect_info["symbol"],
                            "p1_position": f"{p1_pos.sign} {p1_pos.degree:.1f}°",
                            "p2_position": f"{p2_pos.sign} {p2_pos.degree:.1f}°",
                            "exact_angle": target_angle,
                            "actual_angle": angle_diff,
                        }
                    )
                    break  # Нашли аспект, переходим к следующей паре

        return aspect_list

    def _format_aspect(self, aspect: Dict) -> str:
        """Форматирует аспект в читаемую строку."""
        symbol = aspect.get("symbol", "")
        strength_percent = aspect.get("strength", 0)
        orb = aspect.get("orb", 0)

        # Определяем силу аспекта словами
        if strength_percent >= 90:
            strength_word = "точный"
        elif strength_percent >= 70:
            strength_word = "сильный"
        elif strength_percent >= 50:
            strength_word = "средний"
        else:
            strength_word = "слабый"

        return f"{aspect['p1']} {symbol} {aspect['p2']} ({aspect['name']}, {strength_word}, орб {orb:.1f}°)"

    def get_aspect_summary(self, planets: Dict[str, PlanetPosition]) -> str:
        """Возвращает краткое описание аспектов"""
        aspects = self.get_all_aspects(planets, include_minor=False)

        if not aspects:
            return "Значимые аспекты не обнаружены"

        # Подсчитываем аспекты по типам
        soft_count = sum(1 for a in aspects if a["nature"] == "soft")
        hard_count = sum(1 for a in aspects if a["nature"] == "hard")
        neutral_count = sum(1 for a in aspects if a["nature"] == "neutral")

        summary = f"🌟 Аспекты в натальной карте:\n\n"
        summary += f"• Гармоничные аспекты: {soft_count}\n"
        summary += f"• Напряженные аспекты: {hard_count}\n"
        summary += f"• Нейтральные аспекты: {neutral_count}\n\n"

        # Показываем самые сильные аспекты
        summary += "Основные аспекты:\n"
        for i, aspect in enumerate(aspects[:5], 1):
            summary += f"{i}. {self._format_aspect(aspect)}\n"

        return summary

    def find_aspect_patterns(self, planets: Dict[str, PlanetPosition]) -> List[str]:
        """Находит конфигурации аспектов (стеллиумы, большие трины и т.д.)"""
        patterns = []
        aspects = self.get_all_aspects(planets, include_minor=False)

        # Ищем стеллиумы (3+ планеты в соединении)
        conjunctions = [
            a for a in aspects if a["name"] == "Соединение" and a["strength"] >= 70
        ]
        if len(conjunctions) >= 2:
            # Группируем соединения по планетам
            planet_groups = {}
            for conj in conjunctions:
                for planet in [conj["p1"], conj["p2"]]:
                    if planet not in planet_groups:
                        planet_groups[planet] = set()
                    planet_groups[planet].update([conj["p1"], conj["p2"]])

            # Ищем группы из 3+ планет
            for planet, group in planet_groups.items():
                if len(group) >= 3:
                    patterns.append(f"Стеллиум: {', '.join(sorted(group))}")

        # Ищем большие трины (3 планеты в трине друг к другу)
        trines = [a for a in aspects if a["name"] == "Трин" and a["strength"] >= 60]
        if len(trines) >= 3:
            patterns.append("Возможен Большой Трин")

        # Ищем тау-квадраты (оппозиция + 2 квадрата)
        oppositions = [
            a for a in aspects if a["name"] == "Оппозиция" and a["strength"] >= 60
        ]
        squares = [a for a in aspects if a["name"] == "Квадрат" and a["strength"] >= 60]
        if oppositions and len(squares) >= 2:
            patterns.append("Возможен Тау-квадрат")

        return patterns
