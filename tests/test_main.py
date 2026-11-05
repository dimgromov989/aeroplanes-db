"""Тесты консольного меню."""
from unittest.mock import MagicMock, patch

import main
from src.config import COUNTRIES, get_db_params
from src.database import DatabaseError
from src.loader import LoadResult


def run(monkeypatch, inputs):
    """Запускает меню с заданными ответами пользователя."""
    answers = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda _="": next(answers))
    main.user_interaction({"dbname": "test"})


@patch("main.DBManager")
def test_queries(mock_manager, monkeypatch, capsys):
    """Каждый пункт меню вызывает свой метод DBManager."""
    manager = MagicMock()
    mock_manager.return_value.__enter__.return_value = manager
    manager.get_countries_and_aeroplanes_count.return_value = [{"country": "Spain", "aeroplanes_count": 7}]
    manager.get_all_aeroplanes.return_value = []
    manager.get_avg_speed.return_value = 150.0
    manager.get_aeroplanes_with_higher_speed.return_value = []
    manager.get_aeroplanes_with_keyword.return_value = []

    run(monkeypatch, ["2", "3", "4", "5", "6", "IBE", "0"])

    out = capsys.readouterr().out
    assert "Spain" in out and "150.00 м/с" in out and "До свидания!" in out
    manager.get_all_aeroplanes.assert_called_once()
    manager.get_aeroplanes_with_higher_speed.assert_called_once()
    manager.get_aeroplanes_with_keyword.assert_called_once_with("IBE")


@patch("main.DBManager", side_effect=DatabaseError("нет соединения"))
def test_database_error_is_shown(_, monkeypatch, capsys):
    """Ошибка БД выводится пользователю, а программа продолжает работу."""
    run(monkeypatch, ["2", "0"])
    out = capsys.readouterr().out
    assert "Ошибка: нет соединения" in out and "До свидания!" in out


def test_unknown_command(monkeypatch, capsys):
    """Неизвестная команда не приводит к ошибке."""
    run(monkeypatch, ["9", "0"])
    assert "Неизвестная команда" in capsys.readouterr().out


@patch("main.DataLoader")
@patch("main.DBCreator")
def test_load_data(mock_creator, mock_loader, monkeypatch, capsys):
    """Загрузка создает БД и таблицы и обрабатывает все страны."""
    load_countries = mock_loader.return_value.load_countries
    load_countries.return_value = LoadResult({"Spain": 7})

    run(monkeypatch, ["1", "0"])

    mock_creator.return_value.create_database.assert_called_once()
    mock_creator.return_value.create_tables.assert_called_once()
    load_countries.assert_called_once_with(COUNTRIES)
    assert "Spain: сохранено самолетов - 7" in capsys.readouterr().out


def test_countries_count():
    """По критериям в таблице стран должно быть не менее 10 разных значений."""
    assert len(set(COUNTRIES)) >= 10


def test_get_db_params(monkeypatch):
    """Параметры подключения читаются из переменных окружения."""
    monkeypatch.setenv("DB_NAME", "other")
    monkeypatch.setenv("DB_PORT", "6000")
    params = get_db_params()
    assert params["dbname"] == "other" and params["port"] == "6000"
