from dotenv import load_dotenv
from os import getenv
from pathlib import Path

load_dotenv()
AUDIO_STORAGE_API_URL = getenv("AUDIO_STORAGE_API_URL")
API_SECRET_BOT_KEY = getenv("API_SECRET_BOT_KEY")

DB_PATH = Path(__file__).resolve().parent / "users.db"