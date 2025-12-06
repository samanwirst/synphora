import logging
import asyncio
import sys

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

from app.handlers.start_handler import start_router
from app.handlers.audio_handler import audio_router
from app.handlers.room_handler import room_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(start_router)
    dp.include_router(audio_router)
    dp.include_router(room_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())