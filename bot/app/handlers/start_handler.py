from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from utils.api import APIUtils
from utils.user_id_storage import UserIDStorageUtils

start_router = Router()

api = APIUtils()
user_id_storage = UserIDStorageUtils()

@start_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.reply(f"Message ID: {message.message_id}")

    if api.get_user(message.from_user.id) == 404:
        new_uuid = user_id_storage.generate_and_store(message.from_user.id)
        return api.create_user(user_uuid=new_uuid)