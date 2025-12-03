from dotenv import load_dotenv
from os import getenv

load_dotenv()
BOT_TOKEN = getenv("BOT_TOKEN")

# seconds
MIN_AUDIO_DURATION = 60
MAX_AUDIO_DURATION = -1 # means no limit