"""Тесты загрузки данных."""
import pytest

from src.api import AircraftAPI, APIError, GeoAPI
from src.database import DatabaseError
from src.loader import DataLoader
from src.models import Country
from src.storage import BaseStorage


class FakeGeoAPI(GeoAPI):
    """Источник стран, который не знает страну Narnia."""

    def get_country(self, name):
        """Возвращает страну или вызывает APIError."""
        if name == "Narnia":
            raise APIError("Страна не найдена")
        return Country(name, 1, 2, 3, 4)


class FakeAircraftAPI(AircraftAPI):
    """Источник самолетов, недоступный для страны Offline."""

    def __init__(self, planes):
        """Сохраняет самолеты, которые будут возвращаться."""
        self.planes = planes

    def get_aeroplanes(self, country):
        """Возвращает самолеты или вызывает APIError."""
        if country.name == "Offline":
            raise APIError("Сервис недоступен")
        return self.planes


class FakeStorage(BaseStorage):
    """Хранилище в памяти."""

    def __init__(self):
        """Создает пустое хранилище."""
        self.countries = []
        self.aeroplanes = {}

    def save_country(self, country):
        """Запоминает страну."""
        self.countries.append(country.name)
        return len(self.countries)

    def replace_aeroplanes(self, country_id, aeroplanes):
        """Запоминает самолеты страны."""
        self.aeroplanes[country_id] = aeroplanes
        return len(aeroplanes)


def test_load_countries(planes):
    """Сбой по одной стране не мешает загрузить остальные."""
    storage = FakeStorage()
    loader = DataLoader(FakeGeoAPI(), FakeAircraftAPI(planes), storage)
    result = loader.load_countries(["Spain", "Narnia", "Offline", "Italy"])

    assert result.loaded == {"Spain": 4, "Italy": 4}
    assert set(result.failed) == {"Narnia", "Offline"}
    assert storage.countries == ["Spain", "Offline", "Italy"]  # страна сохраняется, даже если opensky недоступен
    assert storage.aeroplanes == {1: planes, 3: planes}


def test_database_error_stops_loading():
    """Ошибка БД не скрывается: продолжать загрузку бессмысленно."""
    class BrokenStorage(FakeStorage):
        """Хранилище, в котором не работает запись."""

        def save_country(self, country):
            """Всегда вызывает ошибку БД."""
            raise DatabaseError("нет соединения")

    with pytest.raises(DatabaseError):
        DataLoader(FakeGeoAPI(), FakeAircraftAPI([]), BrokenStorage()).load_countries(["Spain"])
