"""Тесты вывода в консоль."""
from src.loader import LoadResult
from src.printer import print_aeroplanes, print_avg_speed, print_countries, print_load_result


def make_row(**changes):
    """Создает строку результата запроса о самолете."""
    row = {"country": "Spain", "callsign": "IBE123", "icao24": "a1", "origin_country": "Spain",
           "velocity": 250.5, "altitude": 10000.0, "on_ground": False}
    return {**row, **changes}


def test_print_aeroplanes(capsys):
    """Выводятся нумерация, данные самолета и итог."""
    print_aeroplanes([make_row(), make_row(callsign=None, velocity=None, altitude=None, on_ground=True)])
    out = capsys.readouterr().out
    assert "1. IBE123" in out and "250.50 м/с" in out and "10000.00 м" in out and "в воздухе" in out
    assert "2. нет данных" in out and "на земле" in out and "Всего: 2" in out


def test_print_aeroplanes_empty(capsys):
    """Пустой результат выводится понятным сообщением."""
    print_aeroplanes([])
    assert "Самолеты не найдены" in capsys.readouterr().out


def test_print_countries(capsys):
    """Выводятся страны с количеством самолетов."""
    print_countries([{"country": "Spain", "aeroplanes_count": 7}])
    assert "Spain" in capsys.readouterr().out
    print_countries([])
    assert "Страны не найдены" in capsys.readouterr().out


def test_print_avg_speed(capsys):
    """Средняя скорость выводится с двумя знаками, отсутствие данных - текстом."""
    print_avg_speed(123.456)
    assert "123.46 м/с" in capsys.readouterr().out
    print_avg_speed(None)
    assert "нет данных" in capsys.readouterr().out


def test_print_load_result(capsys):
    """Выводятся и успешные страны, и ошибки."""
    print_load_result(LoadResult({"Spain": 7}, {"Italy": "сбой"}))
    out = capsys.readouterr().out
    assert "Spain: сохранено самолетов - 7" in out and "Italy: ошибка - сбой" in out
