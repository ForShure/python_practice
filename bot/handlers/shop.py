from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from bot.keyboards import categories_keyboard

# Импортируем модели
from shop.models import Product, TelegramUser, Order, News

router = Router()


# --- ПРИВЕТСТВИЕ ---
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await TelegramUser.objects.aget_or_create(
        chat_id=message.chat.id,
        defaults={'username': message.from_user.username}
    )
    kb = [
        [KeyboardButton(text="Каталог"), KeyboardButton(text="🛒 Корзина")],
        [KeyboardButton(text="👤 Профиль")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Добро пожаловать в магазин! 👇", reply_markup=keyboard)


# --- КАТАЛОГ ---
@router.message(F.text == "Каталог")
@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    await message.answer("Выберите категорию:", reply_markup=await categories_keyboard())


# --- ПОКАЗ ТОВАРОВ ---
@router.callback_query(F.data.startswith('category_'))
async def category_click(callback: CallbackQuery):
    category_id = callback.data.split('_')[1]
    products = Product.objects.filter(category_id=category_id)

    await callback.answer()

    # Асинхронная проверка
    if not await products.aexists():
        await callback.message.answer("В этой категории пока пусто 😔")
        return

    BASE_URL = "https://my-shop-bot-service.onrender.com"

    # Асинхронный цикл
    async for product in products:
        text = f"<b>{product.name}</b>\n💰 {product.price}"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Купить", callback_data=f"buy_{product.id}")]
        ])

        if product.image:
            try:
                full_photo_url = f"{BASE_URL}{product.image.url}"
                await callback.message.answer_photo(
                    photo=full_photo_url, caption=text,
                    parse_mode="HTML", reply_markup=kb
                )
            except:
                await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
        else:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)


# --- ПРОФИЛЬ ---
@router.message(F.text == "👤 Профиль")
async def cmd_profile(message: types.Message):
    user_id = message.chat.id
    orders = Order.objects.filter(user_id=user_id).order_by('-created_at')[:5]

    # Асинхронная проверка
    if not await orders.aexists():
        await message.answer("У вас пока нет заказов. 🛍")
        return

    text = "📋 **Ваши последние заказы:**\n\n"

    # Асинхронный цикл
    async for order in orders:
        text += f"🆔 Заказ №{order.id}\n"
        text += f"📅 {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        text += f"Статус: {order.status}\n"
        text += "------------------\n"

    await message.answer(text, parse_mode="Markdown")


# --- НОВОСТИ ---
@router.message(Command("news"))
async def cmd_news(message: types.Message):
    # проверка наличия новостей
    if not await News.objects.aexists():
        await message.answer("Нет новостей")
        return

    # Асинхронный цикл
    async for news in News.objects.all():
        text = f"<b>{news.title}:</b>\t{news.text}"
        await message.answer(text, parse_mode="HTML")
