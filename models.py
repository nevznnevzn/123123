from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple


@dataclass
class Location:
    """Модель локации"""

    city: str
    lat: float
    lng: float
    timezone: str


@dataclass
class BirthData:
    """Модель данных рождения"""

    datetime: datetime
    location: Location


@dataclass
class PlanetPosition:
    """Позиция планеты"""

    sign: str
    degree: float


@dataclass
class UserProfile:
    """Профиль пользователя"""

    user_id: int
    name: str
    birth_data: BirthData
    planets: Dict[str, PlanetPosition]
