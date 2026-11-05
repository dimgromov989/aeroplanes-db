"""Запись данных о странах и самолетах в хранилище."""
from abc import ABC, abstractmethod
from contextlib import closing

import psycopg2
from psycopg2.extras import execute_values

from src.database import DatabaseError, connect
from src.models import Aeroplane, Country


class BaseStorage(ABC):
    """Хранилище, в которое записываются полученные данные."""

    @abstractmethod
    def save_country(self, country: Country) -> int:
        """Сохраняет страну и возвращает ее идентификатор."""

    @abstractmethod
    def replace_aeroplanes(self, country_id: int, aeroplanes: list[Aeroplane]) -> int:
        """Заменяет самолеты страны новыми и возвращает их количество."""


class PostgresStorage(BaseStorage):
    """Записывает данные в таблицы countries и aeroplanes базы PostgreSQL."""

    SAVE_COUNTRY = """
        INSERT INTO countries (name, south, north, west, east)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (name) DO UPDATE
        SET south = EXCLUDED.south, north = EXCLUDED.north, west = EXCLUDED.west, east = EXCLUDED.east
        RETURNING id
    """
    DELETE_AEROPLANES = "DELETE FROM aeroplanes WHERE country_id = %s"
    INSERT_AEROPLANES = """
        INSERT INTO aeroplanes (country_id, icao24, callsign, origin_country, velocity, altitude, on_ground)
        VALUES %s
        ON CONFLICT (country_id, icao24) DO NOTHING
        RETURNING id
    """

    def __init__(self, params: dict[str, str]) -> None:
        """Сохраняет параметры подключения к базе данных."""
        self.__params = params

    def save_country(self, country: Country) -> int:
        """Добавляет страну или обновляет границы уже существующей, возвращает ее id."""
        values = (country.name, country.south, country.north, country.west, country.east)
        with closing(connect(self.__params)) as connection:
            try:
                with connection, connection.cursor() as cursor:
                    cursor.execute(self.SAVE_COUNTRY, values)
                    return cursor.fetchone()[0]
            except psycopg2.Error as error:
                raise DatabaseError(f"Не удалось сохранить страну {country.name}: {error}") from error

    def replace_aeroplanes(self, country_id: int, aeroplanes: list[Aeroplane]) -> int:
        """В одной транзакции заменяет самолеты страны новым снимком воздушного пространства."""
        rows = [
            (country_id, plane.icao24, plane.callsign, plane.origin_country,
             plane.velocity, plane.altitude, plane.on_ground)
            for plane in aeroplanes
        ]
        with closing(connect(self.__params)) as connection:
            try:
                with connection, connection.cursor() as cursor:
                    cursor.execute(self.DELETE_AEROPLANES, (country_id,))
                    return len(execute_values(cursor, self.INSERT_AEROPLANES, rows, fetch=True))
            except psycopg2.Error as error:
                raise DatabaseError(f"Не удалось сохранить самолеты: {error}") from error
