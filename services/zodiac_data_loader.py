import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ZodiacDataLoader:
    """Загружает и хранит астрологические данные из JSON-файла."""

    _instance = None
    _data: Optional[Dict[str, Any]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ZodiacDataLoader, cls).__new__(cls)
            cls._instance.load_data()
        return cls._instance

    def load_data(self, file_path: str = "zodiac_data.json"):
        """Загружает данные из JSON-файла."""
        if self._data is None:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                logger.info(f"Астрологические данные успешно загружены из {file_path}")
            except FileNotFoundError:
                logger.error(f"Файл с данными не найден: {file_path}")
                self._data = {}
            except json.JSONDecodeError:
                logger.error(f"Ошибка декодирования JSON в файле: {file_path}")
                self._data = {}
            except Exception as e:
                logger.error(f"Неизвестная ошибка при загрузке данных: {e}")
                self._data = {}

    def get_description(self, planet_name: str, sign_name: str) -> Optional[str]:
        """
        Получает описание для указанной планеты в указанном знаке зодиака.
        """
        if not self._data or "tables" not in self._data:
            logger.warning("Данные не загружены или имеют неверную структуру.")
            return None

        # Нормализация имен для согласованности
        planet_name_normalized = planet_name.capitalize()
        sign_name_normalized = sign_name.capitalize()

        planet_data = self._data["tables"].get(planet_name_normalized)

        if not planet_data or "data" not in planet_data:
            logger.warning(f"Данные для планеты '{planet_name_normalized}' не найдены.")
            return None

        for record in planet_data["data"]:
            if record.get("zodiac_sign", "").capitalize() == sign_name_normalized:
                return record.get("description")

        logger.warning(
            f"Описание для '{planet_name_normalized}' в знаке '{sign_name_normalized}' не найдено."
        )
        return None


# Создаем единственный экземпляр загрузчика, который будет использоваться во всем приложении
zodiac_data_loader = ZodiacDataLoader()
