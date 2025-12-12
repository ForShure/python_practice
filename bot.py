import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)

API_TOKEN = '123'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Салам алейкум, браза")
async def main():
        await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
