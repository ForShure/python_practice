import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# Настройка Django
sys.path.append(os.path.join(os.getcwd(), 'web'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")
import django

django.setup()

# Импорты (теперь их три!)
from bot.handlers.shop import router as shop_router
from bot.handlers.cart import router as cart_router
from bot.handlers.admin import router as admin_router  # <--- НОВОЕ

# Загрузка .env
env_path = os.path.join(os.getcwd(), 'web', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()


async def main():
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        # Если не нашел TOKEN, попробуем поискать BOT_TOKEN (на всякий случай)
        TOKEN = os.getenv("BOT_TOKEN")

    if not TOKEN:
        print("❌ ОШИБКА: Токен не найден! Проверь .env")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Подключение роутеров
    dp.include_router(shop_router)
    dp.include_router(cart_router)
    dp.include_router(admin_router)  # <--- НОВОЕ

    print("🚀 Бот (Магазин + Админка) запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен.")
