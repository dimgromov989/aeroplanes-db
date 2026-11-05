"""Общие фикстуры тестов."""
import os

import pytest

from src.database import DBCreator, connect
from src.models import Aeroplane, Country


def make_state(icao24="abc123", callsign="IBE123  ", origin="Spain", baro=9000.0, speed=200.0, geo=9100.0):
    """Собирает вектор состояния в формате opensky-network."""
    return [icao24, callsign, origin, 1, 1, -3.7, 40.4, baro, False, speed, 90.0, 0, None, geo, "1000", False, 0]


@pytest.fixture
def spain():
    """Страна для тестов."""
    return Country("Spain", 27.4, 43.9, -18.3, 4.5)


@pytest.fixture
def planes():
    """Самолеты для тестов: средняя скорость известных значений равна 200 м/с."""
    return [
        Aeroplane("a00001", "IBE123", "Spain", 300.0, 11000.0, False),
        Aeroplane("a00002", "ibe456", "Spain", 200.0, 9000.0, False),
        Aeroplane("a00003", "DLH789", "Germany", 100.0, 3000.0, False),
        Aeroplane("a00004", None, "France", None, None, True),
    ]


@pytest.fixture
def db_params():
    """Параметры пустой тестовой БД. Без переменной TEST_DB_PORT тесты с настоящей БД пропускаются."""
    if "TEST_DB_PORT" not in os.environ:
        pytest.skip("Не задан TEST_DB_PORT: нет тестового PostgreSQL")

    params = {
        "host": os.getenv("TEST_DB_HOST", "localhost"),
        "port": os.environ["TEST_DB_PORT"],
        "dbname": "aeroplanes_test",
        "user": os.getenv("TEST_DB_USER", "postgres"),
        "password": os.getenv("TEST_DB_PASSWORD", ""),
    }
    creator = DBCreator(params)
    creator.create_database()
    creator.create_tables()

    connection = connect(params)
    with connection, connection.cursor() as cursor:
        cursor.execute("TRUNCATE countries, aeroplanes RESTART IDENTITY CASCADE")
    connection.close()
    return params
