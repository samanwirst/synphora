from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from utils.api import APIUtils
from utils.room_links import build_listener_room_url, ensure_public_webapp_url, parse_listener_start_payload
from utils.user_id_storage import UserIDStorageUtils

start_router = Router()

api = APIUtils()
user_id_storage = UserIDStorageUtils()

@start_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    if message.from_user is None:
        await message.reply("Cannot resolve Telegram user.")
        return

    user_uuid = user_id_storage.get_user_uuid(message.from_user.id)
    if user_uuid is None:
        new_uuid = user_id_storage.generate_and_store(message.from_user.id)
        try:
            api.create_user(user_uuid=new_uuid)
        except Exception as e:
            await message.reply(f"Failed to initialize account: {e}")
            return

    room_id = parse_listener_start_payload(command.args)
    if room_id is not None:
        try:
            ensure_public_webapp_url()
            listener_url = build_listener_room_url(room_id)
        except Exception as e:
            await message.reply(f"Cannot build listener link: {e}")
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Join as listener", web_app=WebAppInfo(url=listener_url))]
            ]
        )
        try:
            await message.reply(
                f"You were invited to room:\n{room_id}\n\nTap button to join as listener.",
                reply_markup=keyboard,
            )
        except TelegramBadRequest as e:
            await message.reply(
                "Telegram rejected listener Web App URL.\n"
                f"URL: {listener_url}\n"
                f"Error: {e.message}\n\n"
                "Use public HTTPS domain (not localhost) and configure BotFather /setdomain."
            )
        return

    await message.reply(
        "Synphora bot is ready.\n"
        "Send audio files, then use /new_room to start a synced room."
    )
