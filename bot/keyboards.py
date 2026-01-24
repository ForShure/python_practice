from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shop.models import Category


# 1. Добавляем async перед def
async def categories_keyboard():
    buttons = []

    # 2. Используем async for для перебора (это фишка Django)
    async for category in Category.objects.all():
        buttons.append([InlineKeyboardButton(text=category.name, callback_data=f"category_{category.id}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
