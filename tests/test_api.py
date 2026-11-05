"""Тесты клиентов внешних API."""
from unittest.mock import Mock, patch

import pytest
import requests

from src.api import AircraftAPI, APIError, GeoAPI, HTTPClient, NominatimAPI, OpenSkyAPI
from tests.conftest import make_state


def fake_client(answer):
    """Создает HTTP-клиент, который возвращает заданный ответ."""
    client = Mock(spec=HTTPClient)
    client.get_json.return_value = answer
    return client


def test_abstract_classes():
    """Абстрактные классы нельзя создать напрямую."""
    for abstract_class in (GeoAPI, AircraftAPI):
        with pytest.raises(TypeError):
            abstract_class()


@patch("src.api.requests.get")
def test_get_json(mock_get):
    """Успешный запрос возвращает JSON и передает User-Agent."""
    mock_get.return_value = Mock(status_code=200, json=lambda: {"ok": True})
    assert HTTPClient().get_json("http://x", {"a": 1}) == {"ok": True}
    assert "User-Agent" in mock_get.call_args.kwargs["headers"]


@patch("src.api.requests.get")
def test_get_json_errors(mock_get):
    """Ошибки сети, статуса и формата превращаются в APIError."""
    client = HTTPClient()
    mock_get.side_effect = requests.ConnectionError("no network")
    with pytest.raises(APIError, match="Не удалось подключиться"):
        client.get_json("http://x", {})

    mock_get.side_effect = None
    mock_get.return_value = Mock(status_code=429)
    with pytest.raises(APIError, match="429"):
        client.get_json("http://x", {})

    mock_get.return_value = Mock(status_code=200, json=Mock(side_effect=ValueError))
    with pytest.raises(APIError, match="JSON"):
        client.get_json("http://x", {})


def test_nominatim_get_country():
    """Границы страны читаются из boundingbox в порядке юг, север, запад, восток."""
    client = fake_client([{"boundingbox": ["27.4", "43.9", "-18.3", "4.5"]}])
    country = NominatimAPI(client, pause=0).get_country("Spain")
    assert (country.name, country.south, country.north, country.west, country.east) == ("Spain", 27.4, 43.9, -18.3, 4.5)
    assert client.get_json.call_args.args[1]["country"] == "Spain"


@pytest.mark.parametrize("answer", [[], [{}], [{"boundingbox": ["a", "b", "c", "d"]}], [{"boundingbox": ["1"]}]])
def test_nominatim_bad_answer(answer):
    """Если страны нет или ответ некорректен, возникает APIError."""
    with pytest.raises(APIError):
        NominatimAPI(fake_client(answer), pause=0).get_country("Narnia")


def test_opensky_get_aeroplanes(spain):
    """Запрос использует границы страны, а ответ преобразуется в объекты."""
    client = fake_client({"time": 1, "states": [make_state()]})
    planes = OpenSkyAPI(client).get_aeroplanes(spain)
    assert [plane.callsign for plane in planes] == ["IBE123"]
    assert client.get_json.call_args.args[1] == {"lamin": 27.4, "lamax": 43.9, "lomin": -18.3, "lomax": 4.5}


def test_opensky_no_states(spain):
    """Если самолетов нет, opensky возвращает states = null."""
    assert OpenSkyAPI(fake_client({"time": 1, "states": None})).get_aeroplanes(spain) == []


def test_opensky_bad_answer(spain):
    """Ответ неожиданного формата приводит к APIError."""
    with pytest.raises(APIError):
        OpenSkyAPI(fake_client(["unexpected"])).get_aeroplanes(spain)
