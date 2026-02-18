from aiogram import Router
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from aiogram import Bot
from aiogram.utils.deep_linking import create_start_link
import asyncio
import os

from utils.bot_utils import BotUtils
from utils.api import APIUtils
from utils.user_id_storage import UserIDStorageUtils
from utils.file_id_storage import FileIDStorageUtils
from utils.room_links import (
    build_creator_auth_url,
    build_listener_start_payload,
    ensure_public_webapp_url,
)

room_router = Router()

bot_utils = BotUtils()
api = APIUtils()
user_id_storage = UserIDStorageUtils()
file_id_storage = FileIDStorageUtils()

async def download_all_user_audios(bot: Bot, audiolist_uuid: list[str]) -> list[tuple[str, str]]:
    audio_tasks = []
    for track_uuid in audiolist_uuid:
        file_id = file_id_storage.get_file_id(track_uuid)
        if not file_id:
            raise RuntimeError(f"File mapping not found for audio UUID: {track_uuid}")
        task = bot_utils.download_audio_by_file_id(bot=bot, file_id=file_id, filename=track_uuid)
        audio_tasks.append(task)

    return await asyncio.gather(*audio_tasks)

async def upload_all_audios(audio_data: list[tuple[str, str]]) -> None:
    try:
        upload_tasks = [api.upload_audio_file_async(file_path=path, file_name=uuid) for path, uuid in audio_data]
        await asyncio.gather(*upload_tasks)
    finally:
        for path, _ in audio_data:
            if os.path.exists(path):
                os.remove(path)


@room_router.message(Command("new_room"))
async def cmd_new_room(message: Message):
    if message.from_user is None:
        await message.reply("Cannot resolve Telegram user.")
        return

    try:
        ensure_public_webapp_url()
    except Exception as e:
        await message.reply(f"Cannot open Mini App with current CLIENT_APP_URL: {e}")
        return

    user_uuid = user_id_storage.get_user_uuid(message.from_user.id)
    if user_uuid is None:
        await message.reply("Use /start first to initialize your account.")
        return

    user_data = api.get_user(user_uuid)
    if user_data == 404:
        await message.reply("User profile is missing on API. Use /start again.")
        return

    audiolist_uuid = user_data.get("audiolist") or []
    if len(audiolist_uuid) == 0:
        await message.reply("Your playlist is empty. Send audio files first.")
        return

    await message.reply("Preparing a room. Syncing your audio files...")

    try:
        audio_data = await download_all_user_audios(message.bot, audiolist_uuid)
        await upload_all_audios(audio_data)
        room_data = api.create_room(
            creator_user_uuid=user_uuid,
            creator_telegram_id=message.from_user.id,
            track_ids=audiolist_uuid,
        )
        room_id = room_data["room_id"]
        pin_code = room_data["pin_code"]
        creator_auth_url = build_creator_auth_url(room_id)
        listener_start_payload = build_listener_start_payload(room_id)
        listener_invite_link = await create_start_link(message.bot, payload=listener_start_payload, encode=False)
    except Exception as e:
        await message.reply(f"Failed to create a room: {e}")
        return

    await message.reply(
        "Room created.\n"
        f"Room ID: {room_id}\n"
        f"One-time PIN: {pin_code}\n"
        "PIN expires in 24 hours."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Open Creator Auth", web_app=WebAppInfo(url=creator_auth_url))]
        ]
    )
    try:
        await message.reply(
            "Open Mini App auth page and enter PIN to claim the creator control token.",
            reply_markup=keyboard,
        )
    except TelegramBadRequest as e:
        await message.reply(
            "Telegram rejected Web App URL.\n"
            f"URL: {creator_auth_url}\n"
            f"Error: {e.message}\n\n"
            "Use public HTTPS domain (not localhost) and configure BotFather /setdomain."
        )
        return

    await message.reply(
        "Invite link for friends (forward this message):\n"
        f"{listener_invite_link}\n\n"
        "When they open this link, bot will send them a listener button."
    )
