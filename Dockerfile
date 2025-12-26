# Используем легкий Python 3.12
FROM python:3.12-slim

# Настройки, чтобы Python не тупил в контейнере
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Создаем папку внутри контейнера
WORKDIR /app

# Копируем список библиотек и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

CMD ["python", "main.py"]