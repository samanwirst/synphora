from dotenv import load_dotenv
from os import getenv
from pathlib import Path

load_dotenv()

API_SECRET_BOT_KEY = getenv("API_SECRET_BOT_KEY")

FILES_DIR = Path(__file__).resolve().parent / "files"