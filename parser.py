import requests
from bs4 import BeautifulSoup
import time
import json

all_quotes = []

for page in range(1,6):
    url_name = f"http://quotes.toscrape.com/page/{page}/"
    print(f"Парсим станицу {page}")
    time.sleep(1)
    response = requests.get(url_name)
    soup = BeautifulSoup(response.text, "html.parser")
    quotes = soup.find_all("div", class_="quote")

    for quote in quotes:
        text = quote.find("span", class_="text").text.strip('“"')
        author = quote.find("small", class_="author").text
        print(f"{text} - {author}")
        data = {"text": text,
                "author": author}
        all_quotes.append(data)


print(soup.title.text)
print(response.status_code)

with open(".venv/Scripts/all_quotes.json", "w", encoding="utf-8") as file:
    json.dump(all_quotes, file, ensure_ascii=False, indent=4)