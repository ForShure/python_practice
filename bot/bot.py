import asyncio
import logging
import os
import sys
import django

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# НАСТРОЙКА DJANGO
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(current_dir)
web_path = os.path.join(base_dir, 'web')
sys.path.append(web_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

# ИМПОРТЫ ПОСЛЕ ЗАГРУЗКИ DJANGO
dotenv_path = os.path.join(web_path, '.env')
load_dotenv(dotenv_path)

from shop.models import TelegramUser # Нужен для админки
from handlers.user_commands import router as user_router # Импортируем нашего "менеджера"

logging.basicConfig(level=logging.INFO)

admin_id_str = os.getenv('ADMIN_ID')
ADMIN_ID = int(admin_id_str) if admin_id_str else None

API_TOKEN = os.getenv('BOT_TOKEN')

if not API_TOKEN:
    sys.exit("Error: Token not found")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Подключаем роутер (менеджера) к диспетчеру
dp.include_router(user_router)

# АДМИНСКИЕ ФУНКЦИИ (пока оставить тут)
@dp.message(Command("sendall"))
async def cmd_sendall(message: types.Message):
    if message.chat.id == ADMIN_ID:
        text_to_send = message.text.replace('/sendall ', '')
        users = TelegramUser.objects.all()
        for user in users:
            try:
                await bot.send_message(chat_id=user.chat_id, text=text_to_send)
            except:
                pass

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
