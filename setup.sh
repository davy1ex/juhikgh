#!/bin/bash
# Один раз на Raspberry Pi: создаёт venv и ставит зависимости.
# На новых Raspberry Pi OS нельзя pip install в системный Python (PEP 668).
set -e

cd "$(dirname "$0")"

echo "==> Системные пакеты..."
sudo apt update
sudo apt install -y python3-venv python3-pip i2c-tools

echo "==> Виртуальное окружение .venv ..."
python3 -m venv .venv

echo "==> Python-зависимости..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install --default-timeout=100 -r requirements.txt

echo
echo "Готово. Дальше:"
echo "  .venv/bin/python backend/test_servos.py   # тест серво"
echo "  ./start.sh                                 # веб-пульт"
