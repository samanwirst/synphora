from aiogram import F, Router
from aiogram.types import Message

from utils.common import CommonUtils
from utils.api import APIUtils
from utils.user_id_storage import UserIDStorageUtils
from utils.message_id_storage import MessageIDStorageUtils

from config import MIN_AUDIO_DURATION, MAX_AUDIO_DURATION

audio_router = Router()

utils = CommonUtils()
api = APIUtils()
user_id_storage = UserIDStorageUtils()
message_id_storage = MessageIDStorageUtils()

@audio_router.message(F.audio)
async def handle_audio(message: Message):
    audio_duration = message.audio.duration

    if audio_duration < MIN_AUDIO_DURATION:
        await message.reply(f"Audio too short. Minimum length: {utils.format_duration(MIN_AUDIO_DURATION)}.")
        return

    if MAX_AUDIO_DURATION != -1 and audio_duration > MAX_AUDIO_DURATION:
        await message.reply(f"Audio too long. Maximum length: {utils.format_duration(MAX_AUDIO_DURATION)}.")
        return

    user_uuid = user_id_storage.get_user_uuid(message.from_user.id)
    message_uuid = message_id_storage.generate_and_store(message.message_id)
    api.add_audiolist(user_uuid, audiolist=[message_uuid])
    await message.reply(f"Great.\n{message.message_id}")