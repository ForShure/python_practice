import os
from dotenv import load_dotenv
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, LabeledPrice, PreCheckoutQuery, ContentType
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from django.core.exceptions import ObjectDoesNotExist

# Импортируем модели
from shop.models import Product, TelegramUser, CartItem, Order, OrderItem

load_dotenv()
raw_id = str(os.getenv("ADMIN_ID", "0")).strip()
ADMIN_ID = int(raw_id) if raw_id.isdigit() else 0

router = Router()


class OrderState(StatesGroup):
    waiting_for_address = State()


# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ (Генератор текста корзины) ---
# Мы вынесли это отдельно, чтобы использовать и в команде, и в кнопке "Назад"
async def get_cart_data(user):
    cart_items = CartItem.objects.select_related('product').filter(user=user)

    if not await cart_items.aexists():
        return None, None, 0

    total_price = 0
    grouped_items = {}

    # Группируем товары (как мы делали в заказе)
    async for item in cart_items:
        total_price += item.product.price
        p_id = item.product.id
        if p_id in grouped_items:
            grouped_items[p_id]['qty'] += 1
        else:
            grouped_items[p_id] = {
                'name': item.product.name,
                'price': item.product.price,
                'qty': 1
            }

    # Формируем текст
    text = "🛒 **Ваша корзина:**\n\n"
    for p_id, data in grouped_items.items():
        text += f"🔹 {data['name']} x{data['qty']} — {data['price'] * data['qty']} монет\n"

    text += f"\n💰 **Итого: {total_price} монет**"
    return text, grouped_items, total_price


# --- 1. ДОБАВИТЬ В КОРЗИНУ ---
@router.callback_query(F.data.startswith("buy_"))
async def cmd_buy(callback: CallbackQuery):
    product_id = callback.data.split("_")[1]
    try:
        product = await Product.objects.aget(id=product_id)
        user, _ = await TelegramUser.objects.aget_or_create(chat_id=callback.from_user.id)

        await CartItem.objects.acreate(user=user, product=product)
        await callback.answer(f"Добавлено: {product.name}")  # Всплывашка
    except ObjectDoesNotExist:
        await callback.answer("Ошибка товара")


# --- 2. ПОСМОТРЕТЬ КОРЗИНУ (Главное меню) ---
@router.message(F.text == "🛒 Корзина")
async def cmd_cart(message: types.Message):
    user, _ = await TelegramUser.objects.aget_or_create(chat_id=message.chat.id)

    text, grouped_items, total_price = await get_cart_data(user)

    if not text:
        await message.answer("Корзина пуста 🕸")
        return

    # Кнопки управления
    buttons = [
        [InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")],
        [InlineKeyboardButton(text="➖ Удалить товар", callback_data="open_delete_menu")],
        [InlineKeyboardButton(text="🗑 Очистить всё", callback_data="clear")],
    ]
    await message.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


# --- 3. МЕНЮ УДАЛЕНИЯ (Показываем товары кнопками) ---
@router.callback_query(F.data == "open_delete_menu")
async def open_delete_menu(callback: CallbackQuery):
    user = await TelegramUser.objects.aget(chat_id=callback.from_user.id)
    text, grouped_items, total_price = await get_cart_data(user)

    if not text:
        await callback.message.edit_text("Корзина пуста 🕸")
        return

    # Создаем кнопки для каждого товара
    buttons = []
    for p_id, data in grouped_items.items():
        # Кнопка: "Бургер (421)" -> удаляет 1 шт
        btn_text = f"❌ {data['name']} (-1)"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"del_item_{p_id}")])

    # Кнопка Назад
    buttons.append([InlineKeyboardButton(text="🔙 Назад к корзине", callback_data="back_to_cart")])

    await callback.message.edit_text(
        text=text + "\n\n👇 **Нажмите на товар, чтобы удалить 1 шт:**",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# ЛОГИКА УДАЛЕНИЯ ОДНОГО ТОВАРА
@router.callback_query(F.data.startswith("del_item_"))
async def delete_one_item(callback: CallbackQuery):
    # БЫЛО: product_id = callback.data.split("_")[1]
    # СТАЛО: берем [-1] (последний элемент), так надежнее
    product_id = callback.data.split("_")[-1]

    user = await TelegramUser.objects.aget(chat_id=callback.from_user.id)

    # Ищем ОДИН экземпляр этого товара в корзине
    item_to_delete = await CartItem.objects.filter(user=user, product_id=product_id).afirst()

    if item_to_delete:
        await item_to_delete.adelete()
        await callback.answer("Удалено 1 шт.")
        # Перезагружаем меню удаления (обновляем цифры)
        await open_delete_menu(callback)
    else:
        await callback.answer("Этот товар уже удален")
        await open_delete_menu(callback)


# ВЕРНУТЬСЯ В ОБЫЧНУЮ КОРЗИНУ
@router.callback_query(F.data == "back_to_cart")
async def back_to_cart(callback: CallbackQuery):
    user = await TelegramUser.objects.aget(chat_id=callback.from_user.id)
    text, grouped_items, total_price = await get_cart_data(user)

    if not text:
        await callback.message.edit_text("Корзина пуста 🕸")
        return

    buttons = [
        [InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")],
        [InlineKeyboardButton(text="➖ Удалить товар", callback_data="open_delete_menu")],
        [InlineKeyboardButton(text="🗑 Очистить всё", callback_data="clear")],
    ]
    await callback.message.edit_text(text, parse_mode="Markdown",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


# ОЧИСТИТЬ ВСЁ
@router.callback_query(F.data == "clear")
async def process_clear(callback: CallbackQuery):
    user = await TelegramUser.objects.aget(chat_id=callback.from_user.id)
    await CartItem.objects.filter(user=user).adelete()
    await callback.message.edit_text("Корзина очищена! 🗑")
    await callback.answer()


# ОФОРМЛЕНИЕ ЗАКАЗА (Спрашиваем адрес)
@router.callback_query(F.data == "checkout")
async def start_checkout_process(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderState.waiting_for_address)
    await callback.message.answer("🚚 Напишите адрес доставки текстом:")
    await callback.answer()

# ФИНАЛ ОФОРМЛЕНИЯ
@router.message(OrderState.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext):
    try:
        address = message.text
        user = await TelegramUser.objects.aget(chat_id=message.chat.id)

        # Получаем данные из корзины
        text, grouped_items, total_price = await get_cart_data(user)

        if not text:
            await message.answer("Пока вы вводили адрес, корзина опустела!")
            await state.clear()
            return

        # 1. Очищаем текст от Markdown (Telegram Stars не любят звездочки ** в описании)
        clean_text = text.replace("**", "").replace("🛒 ", "").split("\n\n")[0]

        # 2. Отправляем реальный счет
        await message.answer_invoice(
            title="Оплата заказа",
            description=clean_text,
            payload=address,  # Адрес летит скрытым грузом
            currency="XTR",
            prices=[LabeledPrice(label="К оплате", amount=int(total_price))],
            provider_token=""
        )

        await state.clear()

    except Exception as e:
        await message.answer(f"Ошибка оформления: {e}")
        print(f"ERROR: {e}")

# Pre-Checkout
@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


# --- 10. УСПЕШНАЯ ОПЛАТА (Финал) ---
@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def process_payment(message: types.Message, state: FSMContext):
    try:
        # Достаем адрес из "рюкзака", который собрали при создании счета
        address = message.successful_payment.invoice_payload

        user = await TelegramUser.objects.aget(chat_id=message.chat.id)
        text, grouped_items, total_price = await get_cart_data(user)

        # СОЗДАЕМ ЗАКАЗ В БАЗЕ
        order = await Order.objects.acreate(
            user_id=user.chat_id,
            address=address,
            status="Оплачен"  # Сразу ставим статус, что деньги пришли
        )

        # Создаем переменную перед циклом
        admin_items_text = ""

        # Сохраняем товары
        for p_id, data in grouped_items.items():
            await OrderItem.objects.acreate(
                order=order,
                product_name=data['name'],
                price=data['price'],
                quantity=data['qty']
            )
            admin_items_text += f"- {data['name']} x{data['qty']}\n"

        # Чистим корзину
        await CartItem.objects.filter(user=user).adelete()

        await state.clear()

        await message.answer(f"✅ Заказ №{order.id} успешно оплачен!\nСумма: {total_price} ⭐️")

        if ADMIN_ID != 0:
            try:
                await message.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"💸 <b>НОВЫЙ ОПЛАЧЕННЫЙ ЗАКАЗ №{order.id}</b>\n\n"
                         f"👤 Юзер: @{message.from_user.username}\n"
                         f"📍 Адрес: {address}\n"
                         f"💰 Сумма: {total_price} XTR\n\n"
                         f"📦 Товары:\n{admin_items_text}",
                    parse_mode="HTML"
                )
            except:
                pass

    except Exception as e:
        await message.answer(f"Ошибка сохранения: {e}")
        print(f"ERROR: {e}")
