"""Подключение к PostgreSQL и создание базы данных с таблицами."""
from contextlib import closing
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2 import sql

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


class DatabaseError(Exception):
    """Ошибка при работе с базой данных."""


def connect(params: dict[str, str]) -> Any:
    """Открывает соединение с PostgreSQL.

    UnicodeDecodeError возникает, когда сервер на русской Windows возвращает ошибку не в UTF-8.
    """
    try:
        return psycopg2.connect(**params)
    except UnicodeDecodeError as error:
        raise DatabaseError("Не удалось подключиться к PostgreSQL: проверьте параметры в файле .env") from error
    except psycopg2.Error as error:
        raise DatabaseError(f"Не удалось подключиться к PostgreSQL: {error}") from error


class DBCreator:
    """Создает базу данных и таблицы проекта."""

    def __init__(self, params: dict[str, str], schema_path: Path = SCHEMA_PATH) -> None:
        """Сохраняет параметры подключения и путь к SQL-файлу со схемой."""
        self.__params = params
        self.__schema_path = schema_path

    def create_database(self) -> None:
        """Создает базу данных, если ее еще нет."""
        dbname = self.__params["dbname"]
        with closing(connect({**self.__params, "dbname": "postgres"})) as connection:
            connection.autocommit = True  # CREATE DATABASE нельзя выполнить внутри транзакции
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
                    if cursor.fetchone() is None:
                        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            except psycopg2.Error as error:
                raise DatabaseError(f"Не удалось создать базу данных: {error}") from error

    def create_tables(self) -> None:
        """Создает таблицы по схеме из SQL-файла."""
        schema = self.__schema_path.read_text(encoding="utf-8")
        with closing(connect(self.__params)) as connection:
            try:
                with connection, connection.cursor() as cursor:
                    cursor.execute(schema)
            except psycopg2.Error as error:
                raise DatabaseError(f"Не удалось создать таблицы: {error}") from error
