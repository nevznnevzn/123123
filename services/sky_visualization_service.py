import io
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.patches as patches
import matplotlib.patheffects as path_effects

# Графические библиотеки
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Инициализация логгера до всех остальных операций
logger = logging.getLogger(__name__)

from config import Config
from models import Location, PlanetPosition


class SkyVisualizationService:
    """Сервис для создания профессиональных карт звездного неба в стиле референса"""

    # Символы планет (Unicode)
    PLANET_SYMBOLS = {
        "Солнце": "☉",
        "Луна": "☽",
        "Меркурий": "☿",
        "Венера": "♀",
        "Марс": "♂",
        "Юпитер": "♃",
        "Сатурн": "♄",
        "Уран": "♅",
        "Нептун": "♆",
        "Плутон": "♇",
        "Асцендент": "ASC",
    }

    # Символы знаков зодиака
    ZODIAC_SYMBOLS = {
        "Овен": "♈",
        "Телец": "♉",
        "Близнецы": "♊",
        "Рак": "♋",
        "Лев": "♌",
        "Дева": "♍",
        "Весы": "♎",
        "Скорпион": "♏",
        "Стрелец": "♐",
        "Козерог": "♑",
        "Водолей": "♒",
        "Рыбы": "♓",
    }

    # Цветовая схема как в референсе
    COLORS = {
        "background": "#f8f8f8",  # Светло-серый фон
        "chart_bg": "#ffffff",    # Белый фон карты
        "zodiac_circle": "#000000",  # Черные линии зодиака
        "zodiac_text": "#666666",    # Серый текст знаков
        "planet_colors": {
            "Солнце": "#d4a574",     # Золотисто-бежевый
            "Луна": "#c9a876",       # Теплый бежевый
            "Меркурий": "#e6c99a",   # Светло-бежевый
            "Венера": "#ddb882",     # Песочно-бежевый
            "Марс": "#b8956d",       # Темно-бежевый
            "Юпитер": "#c2a373",     # Коричнево-бежевый
            "Сатурн": "#a68b5b",     # Глубокий бежевый
            "Уран": "#d1b689",       # Серо-бежевый
            "Нептун": "#caa678",     # Мягкий бежевый
            "Плутон": "#9d8660",     # Темный бежевый
            "Асцендент": "#c6a876",  # Классический бежевый
        },
        "house_lines": "#cccccc",    # Светло-серые линии домов
        "text": "#333333",           # Темно-серый основной текст
        "title": "#333333",         # Заголовок
        "subtitle": "#666666",      # Подзаголовок
    }

    def __init__(self):
        # Устанавливаем шрифт для поддержки кириллицы
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'Liberation Sans']
        plt.rcParams['axes.unicode_minus'] = False

    async def create_birth_sky_map(
        self,
        birth_date: datetime,
        location: Location,
        planets: Dict[str, PlanetPosition],
        owner_name: str = "Ваше",
        size: int = 1200,
    ) -> bytes:
        """
        Создает профессиональную карту звездного неба в стиле референса

        Args:
            birth_date: Дата и время рождения
            location: Местоположение
            planets: Позиции планет из натальной карты
            owner_name: Имя владельца карты
            size: Размер изображения в пикселях

        Returns:
            bytes: PNG изображение карты неба
        """
        try:
            # Создаем фигуру
            fig_size = size / 100
            fig = plt.figure(figsize=(fig_size, fig_size), facecolor=self.COLORS["background"])
            
            # Создаем основную область для карты
            ax = fig.add_subplot(111, aspect='equal')
            ax.set_xlim(-1.3, 1.3)
            ax.set_ylim(-1.3, 1.3)
            ax.set_facecolor(self.COLORS["background"])
            ax.axis('off')

            # Рисуем основную карту
            self._draw_chart_base(ax)
            self._draw_zodiac_wheel(ax)
            self._draw_house_lines(ax)
            self._draw_planets(ax, planets)
            self._add_title_and_subtitle(fig, birth_date, location, owner_name)
            self._add_decorative_stars(ax)

            # Сохраняем в байты
            buffer = io.BytesIO()
            plt.savefig(
                buffer,
                format="png",
                dpi=150,
                bbox_inches="tight",
                facecolor=self.COLORS["background"],
                edgecolor="none",
                pad_inches=0.2,
            )
            buffer.seek(0)
            plt.close(fig)
            
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Ошибка создания карты неба: {e}")
            return await self._create_error_image(str(e))

    def _draw_chart_base(self, ax):
        """Рисует основную базу карты - круги"""
        # Внешний круг (зодиак)
        outer_circle = plt.Circle((0, 0), 1.0, fill=False, 
                                color=self.COLORS["zodiac_circle"], linewidth=2)
        ax.add_patch(outer_circle)
        
        # Внутренний круг (планеты)
        inner_circle = plt.Circle((0, 0), 0.85, fill=False,
                                color=self.COLORS["zodiac_circle"], linewidth=1)
        ax.add_patch(inner_circle)
        
        # Центральный круг
        center_circle = plt.Circle((0, 0), 0.3, fill=True, 
                                 facecolor=self.COLORS["chart_bg"],
                                 edgecolor=self.COLORS["zodiac_circle"], linewidth=1)
        ax.add_patch(center_circle)

    def _draw_zodiac_wheel(self, ax):
        """Рисует зодиакальное колесо с символами"""
        zodiac_signs = Config.ZODIAC_SIGNS

        for i, sign in enumerate(zodiac_signs):
            # Угол для знака (начинаем с Овна сверху)
            angle = (i * 30 - 90) * np.pi / 180  # -90 чтобы Овен был сверху
            
            # Линии разделения знаков
            x1 = 0.85 * np.cos(angle)
            y1 = 0.85 * np.sin(angle)
            x2 = 1.0 * np.cos(angle)
            y2 = 1.0 * np.sin(angle)
            ax.plot([x1, x2], [y1, y2], color=self.COLORS["zodiac_circle"], linewidth=1)
            
            # Символ знака
            symbol_angle = angle + (15 * np.pi / 180)  # Центр знака
            symbol_x = 1.1 * np.cos(symbol_angle)
            symbol_y = 1.1 * np.sin(symbol_angle)
            
            symbol = self.ZODIAC_SYMBOLS.get(sign, sign[:2])
            ax.text(symbol_x, symbol_y, symbol, fontsize=20, ha='center', va='center',
                   color=self.COLORS["zodiac_text"], fontweight='bold')

    def _draw_house_lines(self, ax):
        """Рисует линии домов (12 секторов)"""
        for i in range(12):
            angle = (i * 30 - 90) * np.pi / 180  # -90 чтобы 1-й дом был внизу
            
            # Линия от центра до внутреннего круга
            x1 = 0
            y1 = 0
            x2 = 0.85 * np.cos(angle)
            y2 = 0.85 * np.sin(angle)
            
            ax.plot([x1, x2], [y1, y2], color=self.COLORS["house_lines"], 
                   linewidth=0.5, alpha=0.7)

    def _draw_planets(self, ax, planets: Dict[str, PlanetPosition]):
        """Рисует планеты на карте"""
        # Список для отслеживания занятых позиций текста
        used_text_positions = []
        
        for planet_name, position in planets.items():
            if planet_name not in self.PLANET_SYMBOLS:
                continue

            # Вычисляем угол планеты
            sign_index = Config.ZODIAC_SIGNS.index(position.sign)
            # Градус внутри знака + базовый угол знака
            total_degrees = sign_index * 30 + position.degree
            # Переводим в радианы, начиная сверху (Овен)
            angle = (total_degrees - 90) * np.pi / 180

            # Радиус для планеты (между внутренним кругом и центром)
            radius = 0.6

            # Позиция планеты
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)

            # Цвет планеты
            color = self.COLORS["planet_colors"].get(planet_name, self.COLORS["text"])

            # Рисуем планету как круг
            planet_circle = plt.Circle((x, y), 0.04, facecolor=color, 
                                     edgecolor='white', linewidth=1, zorder=10)
            ax.add_patch(planet_circle)

            # Символ планеты
            symbol = self.PLANET_SYMBOLS[planet_name]
            ax.text(x, y, symbol, fontsize=12, ha='center', va='center',
                   color='white', fontweight='bold', zorder=11)

            # Находим оптимальную позицию для текста без пересечений
            label_x, label_y = self._find_optimal_text_position(
                x, y, angle, used_text_positions
            )
            
            degree_text = f"{position.degree:.0f}°"
            ax.text(label_x, label_y, f"{planet_name}\n{degree_text}", 
                   fontsize=8, ha='center', va='center',
                   color=self.COLORS["text"], zorder=9)
            
            # Добавляем позицию в список занятых
            used_text_positions.append((label_x, label_y))

    def _find_optimal_text_position(self, planet_x: float, planet_y: float, 
                                   planet_angle: float, used_positions: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Находит оптимальную позицию для текста без пересечений"""
        # Пробуем разные позиции вокруг планеты
        potential_positions = [
            # Основная позиция (перпендикулярно от центра)
            (planet_x + 0.15 * np.cos(planet_angle + np.pi/2), 
             planet_y + 0.15 * np.sin(planet_angle + np.pi/2)),
            # Альтернативная позиция (противоположная сторона)
            (planet_x + 0.15 * np.cos(planet_angle - np.pi/2), 
             planet_y + 0.15 * np.sin(planet_angle - np.pi/2)),
            # Позиция дальше от центра
            (planet_x + 0.2 * np.cos(planet_angle), 
             planet_y + 0.2 * np.sin(planet_angle)),
            # Позиция ближе к центру
            (planet_x - 0.1 * np.cos(planet_angle), 
             planet_y - 0.1 * np.sin(planet_angle)),
            # Диагональные позиции
            (planet_x + 0.12 * np.cos(planet_angle + np.pi/4), 
             planet_y + 0.12 * np.sin(planet_angle + np.pi/4)),
            (planet_x + 0.12 * np.cos(planet_angle - np.pi/4), 
             planet_y + 0.12 * np.sin(planet_angle - np.pi/4)),
        ]
        
        # Минимальное расстояние между текстами
        min_distance = 0.12
        
        for pos_x, pos_y in potential_positions:
            # Проверяем, не слишком ли близко к другим текстам
            too_close = False
            for used_x, used_y in used_positions:
                distance = np.sqrt((pos_x - used_x)**2 + (pos_y - used_y)**2)
                if distance < min_distance:
                    too_close = True
                    break
            
            # Проверяем, не выходит ли за границы карты
            if not too_close and abs(pos_x) < 1.2 and abs(pos_y) < 1.2:
                return pos_x, pos_y
        
        # Если не нашли хорошую позицию, возвращаем основную
        return (planet_x + 0.15 * np.cos(planet_angle + np.pi/2), 
                planet_y + 0.15 * np.sin(planet_angle + np.pi/2))

    def _add_title_and_subtitle(self, fig, birth_date: datetime, location: Location, owner_name: str):
        """Добавляет заголовок и подзаголовок"""
        # Главный заголовок
        title = "Ваше звездное небо"
        fig.suptitle(title, fontsize=24, color=self.COLORS["title"], 
                    fontweight='normal', y=0.92)

        # Подзаголовок с датой и местом
        subtitle = f"{birth_date.strftime('%d.%m.%Y')} в {birth_date.strftime('%H:%M')} {location.city}"
        fig.text(0.5, 0.88, subtitle, fontsize=14, color=self.COLORS["subtitle"],
                ha='center', va='center')

        # Нижняя подпись
        footer = "❅ В этот момент планеты выстроились в уникальный узор,\nкоторый принадлежит только Вам! ❅"
        fig.text(0.5, 0.08, footer, fontsize=10, color=self.COLORS["subtitle"],
                ha='center', va='center', style='italic')

    def _add_decorative_stars(self, ax):
        """Добавляет декоративные звезды на фон"""
        # Генерируем случайные звезды за пределами карты
        np.random.seed(42)  # Для воспроизводимости
        
        n_stars = 30
        # Звезды только за пределами основного круга
        angles = np.random.uniform(0, 2*np.pi, n_stars)
        radii = np.random.uniform(1.15, 1.25, n_stars)  # За пределами зодиака
        
        for angle, radius in zip(angles, radii):
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            
            # Маленькие звездочки
            ax.scatter(x, y, s=8, c='lightgray', marker='*', alpha=0.6)

    async def _create_error_image(self, error_message: str) -> bytes:
        """Создает простое изображение с сообщением об ошибке"""
        try:
            # Создаем простое изображение
            img = Image.new("RGB", (800, 800), color="#f8f8f8")
            draw = ImageDraw.Draw(img)

            # Добавляем текст об ошибке
            draw.text(
                (400, 400),
                f"🌌 Звездное небо\n\n❌ Временно недоступно\n\n{error_message[:50]}...",
                fill="#333333",
                anchor="mm",
            )

            # Сохраняем в байты
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Ошибка создания изображения ошибки: {e}")
            return b""

    async def create_animated_sky_map(
        self,
        birth_date: datetime,
        location: Location,
        planets: Dict[str, PlanetPosition],
        owner_name: str = "Ваше",
    ) -> bytes:
        """
        Создает анимированную версию карты неба (для будущего использования)
        Пока возвращает статичную версию
        """
        return await self.create_birth_sky_map(
            birth_date, location, planets, owner_name
        )

    def _sign_to_degrees(self, sign: str) -> float:
        """Конвертирует знак зодиака в градусы"""
        try:
            sign_index = Config.ZODIAC_SIGNS.index(sign)
            return sign_index * 30
        except ValueError:
            return 0
