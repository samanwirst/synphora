from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
import os

from utils.bot_utils import BotUtils
from utils.api import APIUtils
from utils.user_id_storage import UserIDStorageUtils
from utils.file_id_storage import FileIDStorageUtils

room_router = Router()

bot_utils = BotUtils()
api = APIUtils()
user_id_storage = UserIDStorageUtils()
file_id_storage = FileIDStorageUtils()

async def download_all_user_audios(bot, audiolist_uuid: list[str]) -> list[tuple[str, str]]:
    audio_tasks = []
    for uuid in audiolist_uuid:
        file_id = file_id_storage.get_file_id(uuid)
        task = bot_utils.download_audio_by_file_id(bot=bot, file_id=file_id, filename=uuid)
        audio_tasks.append(task)

    return await asyncio.gather(*audio_tasks)

async def upload_all_audios(audio_data: list[tuple[str, str]]):
    upload_tasks = [api.upload_audio_file(file_path=path, file_name=uuid) for path, uuid in audio_data]
    await asyncio.gather(*upload_tasks)

    for path, _ in audio_data:
        os.remove(path)


@room_router.message(Command("new_room"))
async def cmd_new_room(message: Message):
    user_uuid = user_id_storage.get_user_uuid(message.from_user.id)
    user_data = api.get_user(user_uuid)
    audiolist_uuid = user_data.get("audiolist") or []

    audio_data = await download_all_user_audios(message.bot, audiolist_uuid)
    await message.reply("Downloaded all files locally.")

    await upload_all_audios(audio_data)
    await message.reply("Sent all files to a storage.")