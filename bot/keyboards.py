from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from shop.models import Category

def categories_keyboard():
    # 1. Получаем список всех категорий (множественное число)
    categories = Category.objects.all()
    # 2. Создаем строитель
    keyboard = InlineKeyboardBuilder()
    # 3. Перебираем категории
    for category in categories:
        keyboard.button(text=category.name, callback_data=f"category_{category.id}")
    # 4. Выравниваем
    keyboard.adjust(2)
    return keyboard.as_markup()
