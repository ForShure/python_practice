import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# АСТРОЙКА DJANGO (
sys.path.append(os.path.join(os.getcwd(), 'web'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

# ИМПОРТЫ ПОСЛЕ НАСТРОЙКИ
from bot.handlers.user_commands import router

from django.contrib.auth import get_user_model

async def main():
    # 1. Загружаем переменные
    load_dotenv(os.path.join(os.getcwd(), 'web', '.env'))
    token = os.getenv("BOT_TOKEN")

    # 2. Создаем бота и диспетчер
    bot = Bot(token=token)
    dp = Dispatcher()

    # 3. Подключаем мозги (Роутер)
    dp.include_router(router)

    # 4. Чистим старые сообщения и запускаем
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Бот запущен! Можно писать...")
    await dp.start_polling(bot)


def create_admin():
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():

        User.objects.create_superuser('admin', 'admin@example.com', 'admin_pass_123')
        print("✅ Суперюзер создан!")
    else:
        print("✅ Суперюзер уже есть.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Сначала создаем админа, потом запускаем бота
    create_admin()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
