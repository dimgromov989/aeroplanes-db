"""Получение данных о странах и самолетах из базы данных."""
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from src.database import DatabaseError, connect


class BaseDBManager(ABC):
    """Набор запросов к данным о странах и самолетах."""

    @abstractmethod
    def get_countries_and_aeroplanes_count(self) -> list[dict[str, Any]]:
        """Получает список всех стран и количество самолетов в их воздушных пространствах."""

    @abstractmethod
    def get_all_aeroplanes(self) -> list[dict[str, Any]]:
        """Получает список всех воздушных судов."""

    @abstractmethod
    def get_avg_speed(self) -> float | None:
        """Получает среднюю скорость по самолетам."""

    @abstractmethod
    def get_aeroplanes_with_higher_speed(self) -> list[dict[str, Any]]:
        """Получает список всех самолетов, у которых скорость выше средней."""

    @abstractmethod
    def get_aeroplanes_with_keyword(self, keyword: str) -> list[dict[str, Any]]:
        """Получает список всех самолетов, в позывном которых содержатся переданные символы."""


class DBManager(BaseDBManager):
    """Подключается к базе PostgreSQL и выполняет запросы к ней с помощью psycopg2."""

    AEROPLANES_QUERY = """
        SELECT c.name AS country, a.callsign, a.icao24, a.origin_country, a.velocity, a.altitude, a.on_ground
        FROM aeroplanes AS a
        JOIN countries AS c ON c.id = a.country_id
    """

    def __init__(self, params: dict[str, str]) -> None:
        """Подключается к базе данных."""
        self.__connection = connect(params)
        self.__connection.autocommit = True

    def __enter__(self) -> "DBManager":
        """Возвращает менеджер для использования в блоке with."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Закрывает соединение при выходе из блока with."""
        self.close()

    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        self.__connection.close()

    def __fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """Выполняет запрос и возвращает строки результата в виде словарей."""
        try:
            with self.__connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except psycopg2.Error as error:
            raise DatabaseError(f"Не удалось выполнить запрос: {error}") from error

    def get_countries_and_aeroplanes_count(self) -> list[dict[str, Any]]:
        """Получает все страны, включая страны без самолетов, по убыванию количества самолетов."""
        return self.__fetch_all(
            """
            SELECT c.name AS country, COUNT(a.id) AS aeroplanes_count
            FROM countries AS c
            LEFT JOIN aeroplanes AS a ON a.country_id = c.id
            GROUP BY c.id, c.name
            ORDER BY aeroplanes_count DESC, c.name
            """
        )

    def get_all_aeroplanes(self) -> list[dict[str, Any]]:
        """Получает все самолеты с названием страны, позывным, страной регистрации, скоростью и высотой."""
        return self.__fetch_all(f"{self.AEROPLANES_QUERY} ORDER BY c.name, a.callsign")

    def get_avg_speed(self) -> float | None:
        """Получает среднюю скорость в м/с; самолеты с неизвестной скоростью не учитываются."""
        return self.__fetch_all("SELECT AVG(velocity) AS avg_speed FROM aeroplanes")[0]["avg_speed"]

    def get_aeroplanes_with_higher_speed(self) -> list[dict[str, Any]]:
        """Получает самолеты, летящие быстрее средней скорости, по убыванию скорости."""
        return self.__fetch_all(
            f"""
            {self.AEROPLANES_QUERY}
            WHERE a.velocity > (SELECT AVG(velocity) FROM aeroplanes)
            ORDER BY a.velocity DESC
            """
        )

    def get_aeroplanes_with_keyword(self, keyword: str) -> list[dict[str, Any]]:
        """Получает самолеты, в позывном которых есть переданные символы, без учета регистра."""
        if not keyword.strip():
            raise ValueError("Строка поиска не может быть пустой")

        # Символы % и _ в поисковой строке должны искаться буквально, а не как шаблон LIKE
        escaped = keyword.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return self.__fetch_all(
            f"{self.AEROPLANES_QUERY} WHERE a.callsign ILIKE %s ORDER BY a.callsign, c.name",
            (f"%{escaped}%",),
        )
