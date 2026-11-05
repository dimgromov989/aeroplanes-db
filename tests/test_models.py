"""Тесты моделей."""
import pytest

from src.models import Aeroplane, Country
from tests.conftest import make_state


def test_from_state_strips_callsign():
    """Позывной очищается от пробелов, которыми его дополняет opensky."""
    plane = Aeroplane.from_state(make_state())
    assert plane == Aeroplane("abc123", "IBE123", "Spain", 200.0, 9000.0, False)


@pytest.mark.parametrize("callsign", ["", "   ", None])
def test_from_state_empty_callsign(callsign):
    """Пустой позывной сохраняется как None."""
    assert Aeroplane.from_state(make_state(callsign=callsign)).callsign is None


def test_from_state_altitude_fallback():
    """Если нет барометрической высоты, используется геометрическая."""
    assert Aeroplane.from_state(make_state(baro=None)).altitude == 9100.0
    assert Aeroplane.from_state(make_state(baro=None, geo=None)).altitude is None


def test_cast_to_object_list_skips_invalid():
    """Некорректные записи пропускаются."""
    states = [
        make_state(), make_state(icao24=""), make_state(origin=""),
        make_state(speed=-1), make_state(callsign=5), [1, 2],
    ]
    assert [plane.icao24 for plane in Aeroplane.cast_to_object_list(states)] == ["abc123"]


@pytest.mark.parametrize("name, south, north, west, east", [(" ", 1, 2, 3, 4), ("A", 2, 1, 3, 4), ("A", 1, 2, 4, 3)])
def test_country_validation(name, south, north, west, east):
    """Страна проверяет название и границы."""
    with pytest.raises(ValueError):
        Country(name, south, north, west, east)
