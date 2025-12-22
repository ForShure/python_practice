import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# ---------------------------------------------------------
# ЭТАП 1: Настройка Django (Связываем бота с базой данных)
# ---------------------------------------------------------
sys.path.append(os.path.join(os.getcwd(), 'web'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")

# 👇👇👇 ДОБАВЬ ВОТ ЭТУ СТРОЧКУ СЮДА 👇👇👇
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

# Добавляем папку web в пути, чтобы Python её видел
sys.path.append(os.path.join(os.getcwd(), 'web'))

# Указываем, где лежат настройки Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")

# Запускаем Django (чтобы заработали модели Order, Product и т.д.)
import django

django.setup()

# ---------------------------------------------------------
# ЭТАП 2: Запуск бота (Только ПОСЛЕ запуска Django)
# ---------------------------------------------------------
from aiogram import Bot, Dispatcher
# Импортируем наш файл с логикой (где корзина, адрес и т.д.)
from bot.handlers.user_commands import router


async def main():
    # 1. Загружаем секретные данные из .env
    # Мы ищем .env внутри папки web (или в корне, скрипт поищет везде)
    load_dotenv(os.path.join(os.getcwd(), 'web', '.env'))

    # 2. Достаем токен
    token = os.getenv("BOT_TOKEN")

    if not token:
        print("❌ ОШИБКА: Токен не найден! Проверь, что в .env написано BOT_TOKEN=твои_цифры")
        return

    # 3. Создаем бота
    bot = Bot(token=token)
    dp = Dispatcher()

    # 4. Подключаем "мозги" (наш роутер с командами)
    dp.include_router(router)

    # 5. Удаляем старые обновления (чтобы бот не отвечал на то, что было, пока он спал)
    await bot.delete_webhook(drop_pending_updates=True)

    print("🚀 Бот запущен! Можно писать...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    # Включаем логирование, чтобы видеть ошибки в консоли
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")

