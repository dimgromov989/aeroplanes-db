"""Тесты работы с PostgreSQL. Тесты с фикстурой db_params выполняются на настоящей БД."""
from unittest.mock import MagicMock, patch

import psycopg2
import pytest

from src.database import DatabaseError, DBCreator, connect
from src.db_manager import BaseDBManager, DBManager
from src.models import Aeroplane, Country
from src.storage import BaseStorage, PostgresStorage


@pytest.fixture
def filled_db(db_params, spain, planes):
    """БД с тремя странами: у Spain четыре самолета, у Italy один, у Greece ни одного."""
    storage = PostgresStorage(db_params)
    storage.replace_aeroplanes(storage.save_country(spain), planes)
    italy_id = storage.save_country(Country("Italy", 35, 47, 6, 18))
    storage.replace_aeroplanes(italy_id, [planes[0]])  # тот же самолет виден и над другой страной
    storage.save_country(Country("Greece", 34, 41, 19, 29))
    return db_params


@pytest.fixture
def manager(filled_db):
    """Менеджер, подключенный к заполненной БД."""
    with DBManager(filled_db) as db_manager:
        yield db_manager


def test_abstract_classes():
    """Абстрактные классы нельзя создать напрямую."""
    for abstract_class in (BaseStorage, BaseDBManager):
        with pytest.raises(TypeError):
            abstract_class()


@pytest.mark.parametrize(
    "error",
    [psycopg2.OperationalError("нет сервера"), UnicodeDecodeError("utf-8", b"\xc2", 0, 1, "")],
)
def test_connect_errors(error):
    """Ошибки подключения, в том числе в кодировке русской Windows, превращаются в DatabaseError."""
    with patch("src.database.psycopg2.connect", side_effect=error):
        with pytest.raises(DatabaseError, match="Не удалось подключиться"):
            connect({})


def failing_connection():
    """Создает соединение, курсор которого не может выполнить запрос."""
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg2.ProgrammingError("relation does not exist")
    return connection


@pytest.mark.parametrize(
    "action",
    [
        lambda: DBCreator({"dbname": "x"}).create_database(),
        lambda: DBCreator({"dbname": "x"}).create_tables(),
        lambda: PostgresStorage({}).save_country(Country("Spain", 1, 2, 3, 4)),
        lambda: PostgresStorage({}).replace_aeroplanes(1, []),
        lambda: DBManager({}).get_all_aeroplanes(),
    ],
)
def test_query_errors(action):
    """Ошибки выполнения запросов превращаются в DatabaseError."""
    with patch("src.database.psycopg2.connect", return_value=failing_connection()):
        with pytest.raises(DatabaseError):
            action()


def test_create_tables(db_params):
    """Создаются обе таблицы, повторное создание не приводит к ошибке."""
    creator = DBCreator(db_params)
    creator.create_database()
    creator.create_tables()

    connection = connect(db_params)
    with connection, connection.cursor() as cursor:
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        assert cursor.fetchall() == [("aeroplanes",), ("countries",)]
    connection.close()


def test_save_country_updates_existing(db_params, spain):
    """Повторное сохранение обновляет границы и не создает дубликат."""
    storage = PostgresStorage(db_params)
    first_id = storage.save_country(spain)
    assert storage.save_country(Country("Spain", 1, 2, 3, 4)) == first_id

    connection = connect(db_params)
    with connection, connection.cursor() as cursor:
        cursor.execute("SELECT name, south FROM countries")
        assert cursor.fetchall() == [("Spain", 1.0)]
    connection.close()


def test_replace_aeroplanes(db_params, spain, planes):
    """Новый снимок заменяет старый, повторы внутри снимка отбрасываются, пустой снимок допустим."""
    storage = PostgresStorage(db_params)
    country_id = storage.save_country(spain)
    assert storage.replace_aeroplanes(country_id, planes + planes[:1]) == 4
    assert storage.replace_aeroplanes(country_id, planes[:2]) == 2
    with DBManager(db_params) as db_manager:
        assert len(db_manager.get_all_aeroplanes()) == 2
    assert storage.replace_aeroplanes(country_id, []) == 0


def test_get_countries_and_aeroplanes_count(manager):
    """Все страны попадают в результат, включая страну без самолетов."""
    assert manager.get_countries_and_aeroplanes_count() == [
        {"country": "Spain", "aeroplanes_count": 4},
        {"country": "Italy", "aeroplanes_count": 1},
        {"country": "Greece", "aeroplanes_count": 0},
    ]


def test_get_all_aeroplanes(manager):
    """Возвращаются все самолеты с полной информацией."""
    aeroplanes = manager.get_all_aeroplanes()
    assert len(aeroplanes) == 5
    assert aeroplanes[0] == {
        "country": "Italy", "callsign": "IBE123", "icao24": "a00001", "origin_country": "Spain",
        "velocity": 300.0, "altitude": 11000.0, "on_ground": False,
    }


def test_get_avg_speed(manager):
    """Самолет с неизвестной скоростью не учитывается в среднем."""
    assert manager.get_avg_speed() == pytest.approx((300 + 200 + 100 + 300) / 4)


def test_get_avg_speed_empty(db_params):
    """Для пустой таблицы средней скорости нет."""
    with DBManager(db_params) as db_manager:
        assert db_manager.get_avg_speed() is None


def test_get_aeroplanes_with_higher_speed(manager):
    """Возвращаются только самолеты быстрее среднего, самые быстрые первыми."""
    assert [row["velocity"] for row in manager.get_aeroplanes_with_higher_speed()] == [300.0, 300.0]


def test_get_aeroplanes_with_keyword(manager):
    """Поиск не зависит от регистра и находит символы в любой части позывного."""
    assert [row["callsign"] for row in manager.get_aeroplanes_with_keyword("ibe")] == ["IBE123", "IBE123", "ibe456"]
    assert [row["callsign"] for row in manager.get_aeroplanes_with_keyword(" 78 ")] == ["DLH789"]
    assert manager.get_aeroplanes_with_keyword("ACA") == []


@pytest.mark.parametrize("keyword", ["%", "_", "\\"])
def test_keyword_special_characters(manager, keyword):
    """Символы шаблона LIKE ищутся буквально."""
    assert manager.get_aeroplanes_with_keyword(keyword) == []


def test_keyword_is_literal(db_params, spain):
    """Символ подчеркивания находится только там, где он действительно есть."""
    storage = PostgresStorage(db_params)
    planes = [Aeroplane("b1", "AB_C", "Spain", 1.0, 1.0, False), Aeroplane("b2", "ABXC", "Spain", 1.0, 1.0, False)]
    storage.replace_aeroplanes(storage.save_country(spain), planes)
    with DBManager(db_params) as db_manager:
        assert [row["callsign"] for row in db_manager.get_aeroplanes_with_keyword("B_C")] == ["AB_C"]


@pytest.mark.parametrize("keyword", ["", "   "])
def test_keyword_empty(keyword):
    """Пустая строка поиска не принимается."""
    with patch("src.database.psycopg2.connect"):
        with pytest.raises(ValueError):
            DBManager({}).get_aeroplanes_with_keyword(keyword)


def test_manager_closes_connection():
    """Выход из блока with закрывает соединение."""
    with patch("src.database.psycopg2.connect") as mock_connect:
        with DBManager({}):
            pass
    mock_connect.return_value.close.assert_called_once()
