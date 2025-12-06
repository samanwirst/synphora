import re
from pathlib import Path
from aiogram import Bot

from config import AUDIO_DOWNLOAD_DIR_PATH

class BotUtils:
    @staticmethod
    async def download_audio_by_file_id(bot: Bot, file_id: str, filename: str, save_dir: Path = AUDIO_DOWNLOAD_DIR_PATH) -> tuple[str, str]:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        try:
            file_info = await bot.get_file(file_id)
        except Exception as e:
            raise RuntimeError(f"Failed to get file info for file_id={file_id}: {e}") from e

        file_path = file_info.file_path
        ext = Path(file_path).suffix or ".mp3"

        base = re.sub(r'[\\/*?:"<>|]', "_", filename)
        safe_name = base if Path(base).suffix else f"{base}{ext}"

        local_path = save_dir / safe_name

        try:
            await bot.download_file(file_path, destination=local_path)
        except Exception as e:
            raise RuntimeError(f"Failed to download audio: {e}") from e

        return local_path.as_posix(), safe_name