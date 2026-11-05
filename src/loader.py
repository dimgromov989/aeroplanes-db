"""Заполнение хранилища данными из внешних API."""
from collections.abc import Iterable
from dataclasses import dataclass, field

from src.api import AircraftAPI, APIError, GeoAPI
from src.storage import BaseStorage


@dataclass
class LoadResult:
    """Результат загрузки: количество самолетов по странам и ошибки по странам."""

    loaded: dict[str, int] = field(default_factory=dict)
    failed: dict[str, str] = field(default_factory=dict)


class DataLoader:
    """Получает данные из API и передает их в хранилище."""

    def __init__(self, geo_api: GeoAPI, aircraft_api: AircraftAPI, storage: BaseStorage) -> None:
        """Сохраняет источники данных и хранилище."""
        self.__geo_api = geo_api
        self.__aircraft_api = aircraft_api
        self.__storage = storage

    def load_country(self, name: str) -> int:
        """Загружает страну и ее самолеты, возвращает количество сохраненных самолетов."""
        country = self.__geo_api.get_country(name)
        country_id = self.__storage.save_country(country)
        aeroplanes = self.__aircraft_api.get_aeroplanes(country)
        return self.__storage.replace_aeroplanes(country_id, aeroplanes)

    def load_countries(self, names: Iterable[str]) -> LoadResult:
        """Загружает несколько стран; сбой API по одной стране не останавливает загрузку остальных."""
        result = LoadResult()
        for name in names:
            try:
                result.loaded[name] = self.load_country(name)
            except APIError as error:
                result.failed[name] = str(error)
        return result
