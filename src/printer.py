"""Вывод результатов пользователю в консоль."""
from typing import Any

from src.loader import LoadResult

NO_DATA = "нет данных"


def format_number(value: float | None, unit: str) -> str:
    """Форматирует число с единицей измерения или сообщает об отсутствии данных."""
    return NO_DATA if value is None else f"{value:.2f} {unit}"


def format_aeroplane(aeroplane: dict[str, Any]) -> str:
    """Возвращает строку с информацией о самолете."""
    status = "на земле" if aeroplane["on_ground"] else "в воздухе"
    return (
        f"{aeroplane['callsign'] or NO_DATA:<10} | над страной: {aeroplane['country']:<14} | "
        f"регистрация: {aeroplane['origin_country']:<20} | "
        f"скорость: {format_number(aeroplane['velocity'], 'м/с'):>11} | "
        f"высота: {format_number(aeroplane['altitude'], 'м'):>10} | {status}"
    )


def print_aeroplanes(aeroplanes: list[dict[str, Any]]) -> None:
    """Выводит пронумерованный список самолетов."""
    if not aeroplanes:
        print("Самолеты не найдены.")
        return
    for number, aeroplane in enumerate(aeroplanes, start=1):
        print(f"{number:>5}. {format_aeroplane(aeroplane)}")
    print(f"Всего: {len(aeroplanes)}")


def print_countries(countries: list[dict[str, Any]]) -> None:
    """Выводит страны и количество самолетов в их воздушных пространствах."""
    if not countries:
        print("Страны не найдены.")
    for row in countries:
        print(f"{row['country']:<20} {row['aeroplanes_count']:>6}")


def print_avg_speed(avg_speed: float | None) -> None:
    """Выводит среднюю скорость самолетов."""
    print(f"Средняя скорость: {format_number(avg_speed, 'м/с')}")


def print_load_result(result: LoadResult) -> None:
    """Выводит итог загрузки данных из API."""
    for country, count in result.loaded.items():
        print(f"{country}: сохранено самолетов - {count}")
    for country, error in result.failed.items():
        print(f"{country}: ошибка - {error}")
