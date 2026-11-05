# Самолеты в воздушном пространстве стран: база данных PostgreSQL

Программа получает границы стран через API [nominatim](https://nominatim.org/release-docs/latest/api/Overview/),
а самолеты в этих границах — через API [opensky-network](https://openskynetwork.github.io/opensky-api/rest.html).
Данные сохраняются в PostgreSQL, запросы к ним выполняет класс `DBManager`.

Отслеживаются 12 стран: Spain, Germany, Italy, Poland, United Kingdom, Sweden, Greece, Turkey, India, Japan,
Canada, Brazil. Список можно изменить в [src/config.py](src/config.py).

## Установка и запуск

Нужны Python 3.10+ и запущенный сервер PostgreSQL. Базу данных и таблицы программа создаст сама.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
copy .env.example .env        # Linux / macOS: cp .env.example .env
```

Укажите свои параметры подключения в файле `.env`, затем запустите программу:

```bash
python main.py
```

При первом запуске выберите пункт меню **1**: он создаст базу данных и таблицы и заполнит их данными из API.
Повторная загрузка заменяет самолеты страны новым снимком воздушного пространства.

## Таблицы

**countries** — страны и границы их воздушного пространства.

| Поле | Тип | Описание |
|---|---|---|
| id | SERIAL, PK | идентификатор |
| name | VARCHAR(100), UNIQUE | название страны |
| south, north, west, east | DOUBLE PRECISION | границы из `boundingbox` |

**aeroplanes** — воздушные суда в пространстве страны, связь с `countries` «один ко многим».

| Поле | Тип | Описание |
|---|---|---|
| id | SERIAL, PK | идентификатор |
| country_id | INTEGER, FK → countries.id | страна, над которой находится самолет |
| icao24 | VARCHAR(10) | уникальный код передатчика самолета |
| callsign | VARCHAR(16) | позывной, может отсутствовать |
| origin_country | VARCHAR(100) | страна регистрации |
| velocity | DOUBLE PRECISION | скорость, м/с, может отсутствовать |
| altitude | DOUBLE PRECISION | высота, м, может отсутствовать |
| on_ground | BOOLEAN | находится ли на земле |

Пара `(country_id, icao24)` уникальна. Границы стран прямоугольные и пересекаются, поэтому самолет у границы
учитывается в каждой стране, в прямоугольник которой он попал.

## Класс DBManager

| Метод | Что возвращает |
|---|---|
| `get_countries_and_aeroplanes_count()` | все страны и количество самолетов в них, включая страны без самолетов |
| `get_all_aeroplanes()` | все самолеты: страна, позывной, icao24, страна регистрации, скорость, высота, на земле |
| `get_avg_speed()` | среднюю скорость в м/с, самолеты с неизвестной скоростью не учитываются |
| `get_aeroplanes_with_higher_speed()` | самолеты со скоростью выше средней, по убыванию скорости |
| `get_aeroplanes_with_keyword(keyword)` | самолеты, в позывном которых есть символы `keyword`, без учета регистра |

## Структура проекта

```
├── main.py              # консольное меню, сборка компонентов
├── sql/schema.sql       # таблицы базы данных
├── src/
│   ├── config.py        # список стран, параметры подключения из .env
│   ├── models.py        # Country, Aeroplane
│   ├── api.py           # GeoAPI, AircraftAPI, HTTPClient, NominatimAPI, OpenSkyAPI
│   ├── database.py      # подключение к PostgreSQL, DBCreator - создание БД и таблиц
│   ├── storage.py       # BaseStorage, PostgresStorage - запись в таблицы
│   ├── loader.py        # DataLoader - перенос данных из API в хранилище
│   ├── db_manager.py    # BaseDBManager, DBManager - запросы к данным
│   └── printer.py       # вывод в консоль
└── tests/               # тесты pytest
```

## Принципы SOLID

- **S** — у каждого класса одна задача: `HTTPClient` выполняет запросы, `DBCreator` создает БД, `PostgresStorage`
  записывает, `DBManager` читает, `DataLoader` связывает источники с хранилищем, вывод вынесен в `printer.py`.
- **O** — новый источник данных или хранилище добавляется новым классом-наследником, без изменения `DataLoader`.
- **L** — наследники полностью заменяют свои абстракции: в тестах `DataLoader` работает с поддельными классами.
- **I** — интерфейсы небольшие: источник стран (`GeoAPI`) и источник самолетов (`AircraftAPI`) разделены,
  запись (`BaseStorage`) отделена от чтения (`BaseDBManager`).
- **D** — `DataLoader` и обработчики меню зависят от абстракций, конкретные классы создаются только в `main.py`.

## Тесты

```bash
pytest --cov=src --cov=main --cov-report=term-missing
```

Тесты запросов к БД выполняются на настоящем PostgreSQL и пропускаются, если он не указан. Они используют отдельную
базу `aeroplanes_test`. Чтобы их включить, задайте переменные `TEST_DB_PORT`, а при необходимости `TEST_DB_HOST`,
`TEST_DB_USER` и `TEST_DB_PASSWORD`.
