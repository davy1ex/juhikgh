#!/bin/bash
# Один раз на Raspberry Pi: создаёт venv и ставит зависимости.
# На новых Raspberry Pi OS нельзя pip install в системный Python (PEP 668).
set -e

cd "$(dirname "$0")"

PIP_OPTS=(--default-timeout=100 --retries 5)

echo "==> Системные пакеты..."
sudo apt update
sudo apt install -y python3-venv python3-pip i2c-tools

echo "==> Виртуальное окружение .venv ..."
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi

echo "==> Python-зависимости..."
# pip из venv достаточен; upgrade часто падает на piwheels при плохой сети
.venv/bin/pip install "${PIP_OPTS[@]}" -r requirements.txt

echo
echo "Готово. Дальше:"
echo "  .venv/bin/python backend/test_servos.py   # тест серво"
echo "  ./start.sh                                 # веб-пульт"
