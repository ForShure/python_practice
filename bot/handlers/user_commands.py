import os
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, CallbackQuery, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from django.core.exceptions import ObjectDoesNotExist
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
from bot.keyboards import categories_keyboard

# Загружаем переменные
load_dotenv()

# Надежная загрузка ID
# Считываем как строку, убираем пробелы (.strip)
raw_id = str(os.getenv("ADMIN_ID", "0")).strip()

# Проверяем, состоит ли ID только из цифр
if raw_id.isdigit():
    ADMIN_ID = int(raw_id)
else:
    ADMIN_ID = 0
    print(f"⚠️ ВНИМАНИЕ: ADMIN_ID ('{raw_id}') некорректен! Уведомления приходить не будут.")

# Импортируем модели
from shop.models import Product, News, Order, TelegramUser, CartItem

router = Router()


class OrderState(StatesGroup):
    waiting_for_address = State()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user, created = await TelegramUser.objects.aget_or_create(
        chat_id=message.chat.id,
        defaults={'username': message.from_user.username}
    )
    kb = [
        [KeyboardButton(text="Каталог"), KeyboardButton(text="🛒 Корзина")],
        [KeyboardButton(text="👤 Профиль")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer("Добро пожаловать в магазин! 👇", reply_markup=keyboard)

@router.message(F.text == "Каталог")
@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    await message.answer("Выберите категорию:", reply_markup=categories_keyboard())

@router.message(F.text == "👤 Профиль")
async def cmd_profile(message: types.Message):
    user_id = message.chat.id
    orders = Order.objects.filter(user_id=user_id)

    if not orders.exists():
        await message.answer(f"У вас пока нет заказов. Самое время что-то купить! 🛍")
        return

    text = "📋 **Ваши последние заказы:**\n\n"
    for order in orders:
        text += f"📦 **{order.product.name}**\n"
        # Используем time или created_at (как у тебя в модели)
        text += f"📅 Дата: {order.time.strftime('%Y-%m-%d')}\n"
        text += f"🆔 Номер заказа: {order.id}\n"
        text += "------------------\n"

    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "🛒 Корзина")
async def cmd_cart(message: types.Message):
    try:
        user = TelegramUser.objects.get(chat_id=message.chat.id)
    except ObjectDoesNotExist:
        await message.answer("Сначала нажмите /start")
        return

    cart_items = CartItem.objects.filter(user=user)

    if not cart_items.exists():
        await message.answer("Корзина пуста 🕸")
        return

    text = "🛒 **Ваша корзина:**\n\n"
    total_price = 0

    for item in cart_items:
        text += f"🔹 {item.product.name} — {item.product.price} монет\n"
        total_price += item.product.price

    text += f"\n💰 **Итого: {total_price} монет**"

    buttons = [
        [InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑 Очистить", callback_data="clear")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


@router.callback_query(F.data == "checkout")
async def start_checkout_process(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(OrderState.waiting_for_address)
    await callback.message.answer("🚚 Напишите адрес доставки текстом:")
    await callback.answer()


@router.callback_query(F.data == "clear")
async def process_clear(callback: types.CallbackQuery):
    user = TelegramUser.objects.get(chat_id=callback.from_user.id)
    CartItem.objects.filter(user=user).delete()
    await callback.message.edit_text("Корзина очищена! 🗑")
    await callback.answer()


@router.callback_query(F.data.startswith("buy_"))
async def cmd_buy(callback: types.CallbackQuery):
    product_id = callback.data.split("_")[1]

    try:
        product = Product.objects.get(id=product_id)
        user = TelegramUser.objects.get(chat_id=callback.from_user.id)
        CartItem.objects.create(user=user, product=product)

        await callback.answer(f"Добавлено: {product.name}")
        await callback.message.answer(f"✅ Товар <b>{product.name}</b> добавлен в корзину!", parse_mode="HTML")
    except ObjectDoesNotExist:
        await callback.answer("Ошибка: Товар или пользователь не найден")


@router.message(OrderState.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext):
    try:
        address = message.text
        user = TelegramUser.objects.get(chat_id=message.chat.id)
        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            await message.answer("Корзина пуста!")
            await state.clear()
            return

        total_price = 0
        order_details = ""

        for item in cart_items:
            Order.objects.create(
                user_id=user.chat_id,
                product=item.product,
                address=address
            )
            total_price += item.product.price
            order_details += f"- {item.product.name} ({item.product.price} монеток)\n"

        cart_items.delete()
        await state.clear()

        await message.answer(f"✅ Заказ оформлен!\n🏠 Адрес: {address}\n💰 Сумма: {total_price}")

        # Безопасная отправка Админу
        if ADMIN_ID != 0:
            admin_text = (
                f"🔔 <b>НОВЫЙ ЗАКАЗ!</b>\n\n"
                f"👤 От: @{message.from_user.username} (ID: {message.chat.id})\n"
                f"📦 Состав:\n{order_details}\n"
                f"📍 Адрес: {address}\n"
                f"💵 Итого: {total_price}"
            )
            try:
                await message.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")
            except Exception as e_admin:
                # Если тут ошибка (например, chat not found), бот НЕ упадет, просто напишет в лог
                print(f"❌ ОШИБКА ОТПРАВКИ АДМИНУ: {e_admin}")
        else:
            print("❌ ADMIN_ID не настроен (равен 0), уведомление не отправлено.")

    except Exception as e:
        # Глобальная защита
        await message.answer(f"😱 Ошибка при оформлении: {e}")
        print(f"CRITICAL ERROR: {e}")


@router.callback_query(F.data.startswith('category_'))
async def category_click(callback: CallbackQuery):
    # 1. Получаем ID категории
    category_id = callback.data.split('_')[1]
    # 2. Ищем товары этой категории (filter вместо all)
    products = Product.objects.filter(category_id=category_id)
    # Сообщаем телеграму, что кнопку нажали (чтобы не крутилась загрузка)
    await callback.answer()
    if not products.exists():
        await callback.message.answer("В этой категории пока пусто 😔")
        return
    # 3. Выводим товары (Старый добрый цикл)
    BASE_URL = "https://my-shop-bot-service.onrender.com"
    for product in products:
        text = f"<b>{product.name}</b>\n💰 {product.price}"
        # Кнопка под товаром
        my_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Купить", callback_data=f"buy_{product.id}")]
        ])

        if product.image:
            full_photo_url = f"{BASE_URL}{product.image.url}"
            try:
                await callback.message.answer_photo(
                    photo=full_photo_url, caption=text,
                    parse_mode="HTML", reply_markup=my_keyboard
                )
            except:
                await callback.message.answer(text, parse_mode="HTML", reply_markup=my_keyboard)
        else:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=my_keyboard)

@router.message(Command("news"))
async def cmd_news(message: types.Message):
    news_list = News.objects.all()
    if not news_list:
        await message.answer("Нет новостей")
        return
    for news in news_list:
        text = f"<b>{news.title}:</b>\t{news.text}"
        await message.answer(text, parse_mode="HTML")