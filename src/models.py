"""Модели предметной области: страна и воздушное судно."""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Country:
    """Страна и прямоугольные границы ее воздушного пространства."""

    name: str
    south: float
    north: float
    west: float
    east: float

    def __post_init__(self) -> None:
        """Проверяет название страны и корректность ее границ."""
        if not self.name.strip():
            raise ValueError("Название страны не может быть пустым")
        if self.south > self.north or self.west > self.east:
            raise ValueError(f"Некорректные границы страны {self.name}")


@dataclass(frozen=True)
class Aeroplane:
    """Воздушное судно: скорость в м/с, высота в метрах, неизвестные значения равны None."""

    icao24: str
    callsign: str | None
    origin_country: str
    velocity: float | None
    altitude: float | None
    on_ground: bool

    def __post_init__(self) -> None:
        """Проверяет обязательные поля и значение скорости."""
        if not self.icao24:
            raise ValueError("У самолета должен быть код icao24")
        if not self.origin_country:
            raise ValueError("У самолета должна быть страна регистрации")
        if self.velocity is not None and self.velocity < 0:
            raise ValueError("Скорость не может быть отрицательной")

    @classmethod
    def from_state(cls, state: list[Any]) -> "Aeroplane":
        """Создает самолет из вектора состояния opensky-network.

        Индексы: 0 - icao24, 1 - позывной, 2 - страна регистрации, 7 - барометрическая высота,
        8 - на земле, 9 - скорость, 13 - геометрическая высота.
        """
        callsign = (state[1] or "").strip() or None
        altitude = state[7] if state[7] is not None else state[13]
        return cls(state[0], callsign, state[2], state[9], altitude, bool(state[8]))

    @classmethod
    def cast_to_object_list(cls, states: list[list[Any]]) -> list["Aeroplane"]:
        """Преобразует векторы состояния в список самолетов, пропуская некорректные записи."""
        aeroplanes = []
        for state in states:
            try:
                aeroplanes.append(cls.from_state(state))
            except (AttributeError, IndexError, TypeError, ValueError):
                continue
        return aeroplanes
