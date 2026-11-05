"""Точка входа: консольное меню программы."""
from src.api import HTTPClient, NominatimAPI, OpenSkyAPI
from src.config import COUNTRIES, get_db_params
from src.database import DatabaseError, DBCreator
from src.db_manager import BaseDBManager, DBManager
from src.loader import DataLoader
from src.printer import print_aeroplanes, print_avg_speed, print_countries, print_load_result
from src.storage import PostgresStorage

MENU = """
Выберите действие:
1 - Создать базу данных и загрузить данные из API
2 - Страны и количество самолетов
3 - Все самолеты
4 - Средняя скорость
5 - Самолеты со скоростью выше средней
6 - Поиск самолетов по позывному
0 - Выход"""


def load_data(params: dict[str, str]) -> None:
    """Создает базу данных с таблицами и заполняет их данными из API."""
    creator = DBCreator(params)
    creator.create_database()
    creator.create_tables()

    client = HTTPClient()
    loader = DataLoader(NominatimAPI(client), OpenSkyAPI(client), PostgresStorage(params))
    print("Загружаем данные, это займет около минуты...")
    print_load_result(loader.load_countries(COUNTRIES))


def show_countries(manager: BaseDBManager) -> None:
    """Выводит страны и количество самолетов в них."""
    print_countries(manager.get_countries_and_aeroplanes_count())


def show_all_aeroplanes(manager: BaseDBManager) -> None:
    """Выводит все самолеты."""
    print_aeroplanes(manager.get_all_aeroplanes())


def show_avg_speed(manager: BaseDBManager) -> None:
    """Выводит среднюю скорость самолетов."""
    print_avg_speed(manager.get_avg_speed())


def show_faster_aeroplanes(manager: BaseDBManager) -> None:
    """Выводит самолеты со скоростью выше средней."""
    print_aeroplanes(manager.get_aeroplanes_with_higher_speed())


def show_by_keyword(manager: BaseDBManager) -> None:
    """Запрашивает символы и выводит самолеты, в позывном которых они содержатся."""
    keyword = input("Введите символы позывного (например, IBE): ")
    print_aeroplanes(manager.get_aeroplanes_with_keyword(keyword))


QUERIES = {
    "2": show_countries,
    "3": show_all_aeroplanes,
    "4": show_avg_speed,
    "5": show_faster_aeroplanes,
    "6": show_by_keyword,
}


def handle_choice(choice: str, params: dict[str, str]) -> None:
    """Выполняет выбранный пункт меню."""
    if choice == "1":
        load_data(params)
    elif choice in QUERIES:
        with DBManager(params) as manager:
            QUERIES[choice](manager)
    else:
        print("Неизвестная команда, попробуйте еще раз.")


def user_interaction(params: dict[str, str]) -> None:
    """Показывает меню и обрабатывает выбор пользователя до выхода из программы."""
    print("Программа для отслеживания самолетов в воздушном пространстве стран")
    while True:
        print(MENU)
        choice = input("Ваш выбор: ").strip()
        if choice == "0":
            print("До свидания!")
            break
        try:
            handle_choice(choice, params)
        except (DatabaseError, ValueError) as error:
            print(f"Ошибка: {error}")


if __name__ == "__main__":
    user_interaction(get_db_params())
