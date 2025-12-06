from dotenv import load_dotenv
from os import getenv
from pathlib import Path

load_dotenv()
BOT_TOKEN = getenv("BOT_TOKEN")
SERVER_API_URL = getenv("SERVER_API_URL")
AUDIO_STORAGE_API_URL = getenv("AUDIO_STORAGE_API_URL")
API_SECRET_BOT_KEY = getenv("API_SECRET_BOT_KEY")

# seconds
MIN_AUDIO_DURATION = 60
MAX_AUDIO_DURATION = -1 # means no limit

USER_ID_STORAGE_PATH = Path(__file__).resolve().parent / "user_id_storage.db"
FILE_ID_STORAGE_PATH = Path(__file__).resolve().parent / "file_id_storage.db"
AUDIO_DOWNLOAD_DIR_PATH = Path(__file__).resolve().parent / "downloads"