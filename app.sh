#!/bin/bash

# Останавливаем скрипт при ошибке
set -e

# Проверяем, есть ли файл с виртуальной средой
if [ ! -d "myvenv" ]; then
    echo "Создание виртуальной среды..."
    python3 -m venv myvenv
fi

# Активируем виртуальную среду
source myvenv/bin/activate

# Устанавливаем зависимости, если их нет
if [ ! -f "myvenv/lib/python$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')/site-packages/aiogram" ]; then
    echo "Установка зависимостей..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Запуск скрипта week.py
echo "Запуск Telegram-бота..."
python week.py
