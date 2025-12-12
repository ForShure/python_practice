import asyncio
import logging
import random
import requests
import sqlite3
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)

bot = Bot(token='123')
dp = Dispatcher()

def db_start():
    connect = sqlite3.connect('test.db')
    cursor = connect.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
    connect.commit()
    cursor.close()
    connect.close()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    connect = sqlite3.connect('test.db')
    cursor = connect.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (message.from_user.id, message.from_user.first_name))
    connect.commit()
    print(f"Сохранил юзера: {message.from_user.first_name}")
    cursor.close()
    connect.close()
    await message.answer(f"Салам алейкум, браза, напиши /quote")

@dp.message (Command('quote'))
async def cmd_quote(message: types.Message):
    await message.answer(f"В поисках цитаты")

    url = "http://quotes.toscrape.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    quotes = soup.find_all("div", class_="quote")

    random_quote = random.choice(quotes)

    text = random_quote.find("span", class_="text").text
    author = random_quote.find("small", class_="author").text

    await message.answer(f"{text} - {author}")

@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    connect = sqlite3.connect('test.db')
    cursor = connect.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    s = "Список юзеров:\n"
    for user in users:
        s += f"{user[0]} - {user[1]}\n"
    cursor.close()
    connect.close()
    await message.answer(s)


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    db_start()
    asyncio.run(main())







