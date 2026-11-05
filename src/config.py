"""Настройки проекта: отслеживаемые страны и параметры подключения к БД."""
import os

from dotenv import load_dotenv

# Франции здесь нет намеренно: из-за заморских территорий ее boundingbox покрывает почти весь мир.
COUNTRIES = (
    "Spain",
    "Germany",
    "Italy",
    "Poland",
    "United Kingdom",
    "Sweden",
    "Greece",
    "Turkey",
    "India",
    "Japan",
    "Canada",
    "Brazil",
)


def get_db_params() -> dict[str, str]:
    """Возвращает параметры подключения к PostgreSQL из файла .env и переменных окружения."""
    load_dotenv()
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "aeroplanes"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }
