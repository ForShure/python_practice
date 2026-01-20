from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from django.core.exceptions import ObjectDoesNotExist
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Импортируем модели (Джанго уже будет настроен в главном файле)
from shop.models import Product, News, Order, TelegramUser, CartItem

# Создаем Роутер (это "отдел" по работе с пользователями)
router = Router()

class OrderState(StatesGroup):
    waiting_for_address = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user, created = TelegramUser.objects.get_or_create(
        chat_id=message.chat.id,
        defaults={'username': message.from_user.username}
    )
    # 👇 ДОБАВИЛ КНОПКУ "КОРЗИНА"
    kb = [
        [KeyboardButton(text="Каталог"), KeyboardButton(text="🛒 Корзина")],
        [KeyboardButton(text="👤 Профиль")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    if created:
        await message.answer(f"Добро пожаловать 👇", reply_markup=keyboard)
    else:
        await message.answer(f"С возвращением 👇", reply_markup=keyboard)


@router.message(F.text == "Каталог")
@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    products = Product.objects.all()

    if not products:
        await message.answer("Магазин пуст")
        return

    for product in products:
        text = (
            f"<b>{product.name}</b>\n"
            f"💰 Цена: {product.price}\n"
            f"📜 {product.description}\n"
        )
        my_button = InlineKeyboardButton(text="Купить", callback_data=f"buy_{product.id}")
        my_keyboard = InlineKeyboardMarkup(inline_keyboard=[[my_button]])

        if product.image:
            photo_file = FSInputFile(product.image.path)
            await message.answer_photo(photo_file, caption=text, parse_mode="HTML", reply_markup=my_keyboard)
        else:
            await message.answer(text, parse_mode="HTML", reply_markup=my_keyboard)


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
        # Проверь, как у тебя точно называется поле (time или created_at)
        text += f"📅 Дата: {order.time.strftime('%Y-%m-%d')}\n"
        text += f"🆔 Номер заказа: {order.id}\n"
        text += "------------------\n"

    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "🛒 Корзина")
async def cmd_cart(message: types.Message):
    # 1. Находим юзера (правильно, через chat_id)
    try:
        user = TelegramUser.objects.get(chat_id=message.chat.id)
    except ObjectDoesNotExist:
        await message.answer("Сначала нажмите /start")
        return

    # 2. Достаем товары (используем найденный объект user)
    cart_items = CartItem.objects.filter(user=user)

    if not cart_items.exists():
        await message.answer("Корзина пуста 🕸")
        return

    text = "🛒 **Ваша корзина:**\n\n"
    total_price = 0

    for item in cart_items:
        text += f"🔹 {item.product.name} — {item.product.price} монет\n"
        total_price += item.product.price  # Накапливаем сумму отдельно

    text += f"\n💰 **Итого: {total_price} монет**"

    buttons =[
        [InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑 Очистить", callback_data="clear")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


@router.callback_query(F.data == "checkout")
async def start_checkout_process(callback: types.CallbackQuery, state: FSMContext):
    # Включаем режим ожидания
    await state.set_state(OrderState.waiting_for_address)

    # Спрашиваем адрес
    await callback.message.answer("🚚 Напишите адрес доставки текстом:")

    # Отвечаем на нажатие кнопки
    await callback.answer()

@router.callback_query(F.data == "clear")
async def process_clear(callback: types.CallbackQuery):
    # 1. Находим юзера
    user = TelegramUser.objects.get(chat_id=callback.from_user.id)

    # 2. Удаляем товары этого юзера
    CartItem.objects.filter(user=user).delete()

    # 3. Меняем текст сообщения, чтобы юзер видел результат
    await callback.message.edit_text("Корзина очищена! 🗑")
    # Не забываем отвечать на колбэк, чтобы кнопка не "крутилась"
    await callback.answer()

@router.callback_query(F.data.startswith("buy_"))
async def cmd_buy(callback: types.CallbackQuery):
    product_id = callback.data.split("_")[1]

    try:
        product = Product.objects.get(id=product_id)
        user = TelegramUser.objects.get(chat_id=callback.from_user.id)
    except ObjectDoesNotExist:
        await callback.answer("Ошибка: Товар или пользователь не найден")
        return

    CartItem.objects.create(user=user, product=product)

    await callback.answer(f"Добавлено: {product.name}")
    await callback.message.answer(f"✅ Товар <b>{product.name}</b> добавлен в корзину!", parse_mode="HTML")


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
        order_details = "" # Собираем текст для уведомления админа

        for item in cart_items:
            # Создаем заказ в базе С АДРЕСОМ
            Order.objects.create(
                user_id=user.chat_id,
                product=item.product,
                address=address # Теперь адрес сохранится в Django!
            )
            total_price += item.product.price
            order_details += f"- {item.product.name} ({item.product.price} монеток)\n"

        # Очищаем корзину и состояние
        cart_items.delete()
        await state.clear()

        # 1. Ответ пользователю
        await message.answer(f"✅ Заказ оформлен!\n🏠 Адрес: {address}\n💰 Сумма: {total_price}")

        # 2. УВЕДОМЛЕНИЕ АДМИНУ
        admin_text = (
            f"🔔 <b>НОВЫЙ ЗАКАЗ!</b>\n\n"
            f"👤 От: @{message.from_user.username} (ID: {message.chat.id})\n"
            f"📦 Состав:\n{order_details}\n"
            f"📍 Адрес: {address}\n"
            f"💵 Итого: {total_price}"
        )
        await message.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"😱 Ошибка: {e}")

@router.message(Command("news"))
async def cmd_news(message: types.Message):
    news_list = News.objects.all()
    if not news_list:
        await message.answer("Нет новостей")
        return
    for news in news_list:
        text = f"<b>{news.title}:</b>\t{news.text}"
        await message.answer(text, parse_mode="HTML")