from aiogram import F, Router
from aiogram.types import Message

from config import MIN_AUDIO_DURATION, MAX_AUDIO_DURATION
from utils.common import format_duration

audio_router = Router()

@audio_router.message(F.audio)
async def handle_audio(message: Message):
    audio_duration = message.audio.duration

    if audio_duration < MIN_AUDIO_DURATION:
        await message.reply(f"Audio too short. Minimum length: {format_duration(MIN_AUDIO_DURATION)}.")
        return

    if MAX_AUDIO_DURATION != -1 and audio_duration > MAX_AUDIO_DURATION:
        await message.reply(f"Audio too long. Maximum length: {format_duration(MAX_AUDIO_DURATION)}.")
        return

    await message.reply("Great.")