from dotenv import load_dotenv
from os import getenv
from pathlib import Path

load_dotenv()
BOT_TOKEN = getenv("BOT_TOKEN")
API_URL = getenv("API_URL")
API_SECRET_BOT_KEY = getenv("API_SECRET_BOT_KEY")

# seconds
MIN_AUDIO_DURATION = 60
MAX_AUDIO_DURATION = -1 # means no limit

ID_STORAGE_PATH = Path(__file__).resolve().parent / "id_storage.db"