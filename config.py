import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


class EnvIsNotDefined(Exception):
    def __init__(self, key: str):
        super().__init__(f"environment variable {key} is not defined")


def env_required(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvIsNotDefined(key)
    return value


def env_with_default(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass
class Config:
    telegram_bot_token: str
    admin_ids: list[int]
    logs_dir: str
    db_uri: str
    capacity: int
    rsvp_window_hours: int


config = Config(
    telegram_bot_token=env_required("TELEGRAM_BOT_TOKEN"),
    admin_ids=list(map(int, env_required("ADMIN_IDS").split(";"))),
    logs_dir=env_with_default("LOGS_DIR", "./logs"),
    db_uri=env_with_default("DATABASE_URI", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres?sslmode=disable"),
    capacity=int(env_with_default("CAPACITY", "80")),
    rsvp_window_hours=int(env_with_default("RSVP_WINDOW_HOURS", "48")),
)
