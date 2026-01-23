#!/bin/bash
# Добавляем папку web в список мест, где Python ищет файлы
export PYTHONPATH=$PYTHONPATH:./web
gunicorn web.web.wsgi:application --bind 0.0.0.0:$PORT &
python main.py