#!/bin/bash
gunicorn web.web.wsgi:application --bind 0.0.0.0:$PORT &
python main.py