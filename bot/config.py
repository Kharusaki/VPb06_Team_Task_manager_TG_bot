import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Создайте файл .env и добавьте BOT_TOKEN=ваш_токен")

DATABASE_PATH: str = str(BASE_DIR / "tasks.db")
