"""Клиенты внешних API: nominatim (координаты стран) и opensky-network (самолеты)."""
import time
from abc import ABC, abstractmethod
from typing import Any

import requests

from src.models import Aeroplane, Country


class APIError(Exception):
    """Ошибка при обращении к внешнему API."""


class GeoAPI(ABC):
    """Источник географических данных о странах."""

    @abstractmethod
    def get_country(self, name: str) -> Country:
        """Возвращает страну с границами ее воздушного пространства."""


class AircraftAPI(ABC):
    """Источник данных о самолетах."""

    @abstractmethod
    def get_aeroplanes(self, country: Country) -> list[Aeroplane]:
        """Возвращает самолеты, находящиеся в воздушном пространстве страны."""


class HTTPClient:
    """Выполняет GET-запросы и возвращает разобранный JSON-ответ."""

    HEADERS = {"User-Agent": "aeroplanes-coursework/1.0 (educational project)"}

    def __init__(self, timeout: int = 30) -> None:
        """Сохраняет таймаут запроса в секундах."""
        self.__timeout = timeout

    def get_json(self, url: str, params: dict[str, Any]) -> Any:
        """Выполняет запрос и возвращает JSON; при любой ошибке вызывает APIError."""
        try:
            response = requests.get(url, params=params, headers=self.HEADERS, timeout=self.__timeout)
        except requests.RequestException as error:
            raise APIError(f"Не удалось подключиться к {url}: {error}") from error

        if response.status_code != 200:
            raise APIError(f"Сервис {url} вернул ошибку {response.status_code}")

        try:
            return response.json()
        except ValueError as error:
            raise APIError(f"Сервис {url} вернул некорректный JSON") from error


class NominatimAPI(GeoAPI):
    """Получает границы стран из nominatim.openstreetmap.org."""

    URL = "https://nominatim.openstreetmap.org/search"

    def __init__(self, client: HTTPClient, pause: float = 1.0) -> None:
        """Сохраняет HTTP-клиент и паузу между запросами: сервис разрешает не более одного запроса в секунду."""
        self.__client = client
        self.__pause = pause

    def get_country(self, name: str) -> Country:
        """Запрашивает страну по названию и возвращает ее границы из поля boundingbox."""
        data = self.__client.get_json(self.URL, {"country": name, "format": "json", "limit": 1})
        time.sleep(self.__pause)
        if not data:
            raise APIError(f"Страна '{name}' не найдена")

        try:
            south, north, west, east = (float(coordinate) for coordinate in data[0]["boundingbox"])
            return Country(name, south, north, west, east)
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise APIError(f"Не удалось получить координаты страны '{name}'") from error


class OpenSkyAPI(AircraftAPI):
    """Получает самолеты в заданном прямоугольнике из opensky-network.org."""

    URL = "https://opensky-network.org/api/states/all"

    def __init__(self, client: HTTPClient) -> None:
        """Сохраняет HTTP-клиент."""
        self.__client = client

    def get_aeroplanes(self, country: Country) -> list[Aeroplane]:
        """Запрашивает состояния самолетов в границах страны и преобразует их в объекты."""
        params = {"lamin": country.south, "lamax": country.north, "lomin": country.west, "lomax": country.east}
        data = self.__client.get_json(self.URL, params)
        if not isinstance(data, dict):
            raise APIError("Некорректный ответ от opensky-network")
        return Aeroplane.cast_to_object_list(data.get("states") or [])
