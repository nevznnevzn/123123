from unittest.mock import Mock, patch

import pytest

from models import Location
from services.geocoding_service import GeocodingService


class TestGeocodingService:
    """Тесты для сервиса геокодирования"""

    def test_init_creates_required_objects(self):
        """Тест: инициализация создает необходимые объекты"""
        service = GeocodingService()

        assert service.geolocator is not None
        assert service.tf is not None
        assert hasattr(service.geolocator, "geocode")

    @patch("geopy.geocoders.Nominatim.geocode")
    @patch("timezonefinder.TimezoneFinder.timezone_at")
    def test_get_coordinates_success(self, mock_timezone_at, mock_geocode):
        """Тест: успешное получение координат"""
        # Настройка моков
        mock_location = Mock()
        mock_location.latitude = 55.7558
        mock_location.longitude = 37.6176
        mock_location.address = "Москва, Россия"
        mock_geocode.return_value = mock_location
        mock_timezone_at.return_value = "Europe/Moscow"

        service = GeocodingService()
        result = service.get_coordinates("Москва")

        assert result is not None
        assert result["city"] == "Москва"
        assert result["lat"] == 55.7558
        assert result["lng"] == 37.6176
        assert result["timezone"] == "Europe/Moscow"
        assert result["address"] == "Москва, Россия"

    @patch("geopy.geocoders.Nominatim.geocode")
    def test_get_coordinates_city_not_found(self, mock_geocode):
        """Тест: город не найден"""
        mock_geocode.return_value = None

        service = GeocodingService()
        result = service.get_coordinates("НесуществующийГород")

        assert result is None

    @patch("geopy.geocoders.Nominatim.geocode")
    def test_get_coordinates_exception(self, mock_geocode):
        """Тест: обработка исключений"""
        mock_geocode.side_effect = Exception("Сетевая ошибка")

        service = GeocodingService()
        result = service.get_coordinates("Москва")

        assert result is None

    @patch.object(GeocodingService, "get_coordinates")
    def test_get_location_success(self, mock_get_coordinates):
        """Тест: успешное создание объекта Location"""
        mock_get_coordinates.return_value = {
            "city": "Москва",
            "lat": 55.7558,
            "lng": 37.6176,
            "timezone": "Europe/Moscow",
        }

        service = GeocodingService()
        location = service.get_location("Москва")

        assert isinstance(location, Location)
        assert location.city == "Москва"
        assert location.lat == 55.7558
        assert location.lng == 37.6176
        assert location.timezone == "Europe/Moscow"

    @patch.object(GeocodingService, "get_coordinates")
    def test_get_location_failure(self, mock_get_coordinates):
        """Тест: неудачное получение Location"""
        mock_get_coordinates.return_value = None

        service = GeocodingService()
        location = service.get_location("НесуществующийГород")

        assert location is None


if __name__ == "__main__":
    pytest.main([__file__])
