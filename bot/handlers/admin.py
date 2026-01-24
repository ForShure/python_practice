import os
from aiogram import Router, types
from aiogram.filters import Command
from shop.models import TelegramUser
from dotenv import load_dotenv

load_dotenv()
# Получаем ID админа
raw_id = str(os.getenv("ADMIN_ID", "0")).strip()
ADMIN_ID = int(raw_id) if raw_id.isdigit() else 0

router = Router()


@router.message(Command("sendall"))
async def cmd_sendall(message: types.Message):
    # Проверка: команду может запускать ТОЛЬКО админ
    if message.chat.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав на эту команду.")
        return

    # Убираем саму команду из текста, оставляем сообщение
    text_to_send = message.text.replace('/sendall', '').strip()

    if not text_to_send:
        await message.answer("⚠️ Введите текст рассылки.\nПример: /sendall Скидки на бургеры!")
        return

    await message.answer(f"📤 Начинаю рассылку: {text_to_send}")

    users = TelegramUser.objects.all()
    count = 0
    for user in users:
        try:
            await message.bot.send_message(chat_id=user.chat_id, text=text_to_send)
            count += 1
        except Exception as e:
            # Если бот заблокирован пользователем, будет ошибка. Игнорируем.
            pass

    await message.answer(f"✅ Рассылка завершена! Получили: {count} чел.")