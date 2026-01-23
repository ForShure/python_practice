#!/bin/bash
gunicorn web.wsgi:application --bind 0.0.0.0:$PORT &
python main.py