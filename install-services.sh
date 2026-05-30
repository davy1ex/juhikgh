#!/bin/bash
# Устанавливает автозапуск пульта и Wi‑Fi точку доступа (systemd, до логина в систему).
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="${SUDO_USER:-$(whoami)}"
HOME_DIR="$(getent passwd "$USER_NAME" | cut -d: -f6)"

if [ "$(id -u)" -ne 0 ]; then
  echo "Запусти с sudo: sudo ./install-services.sh"
  exit 1
fi

if [ ! -x "$PROJECT_DIR/.venv/bin/python" ]; then
  echo "Не найден: $PROJECT_DIR/.venv/bin/python"
  echo
  if [ ! -f "$PROJECT_DIR/setup.sh" ]; then
    echo "Нет setup.sh. Подтяни код: cd $PROJECT_DIR && git pull"
    exit 1
  fi
  echo "Сначала нужны Python-зависимости (venv). Без sudo:"
  echo "  cd $PROJECT_DIR && ./setup.sh"
  echo
  read -r -p "Запустить setup.sh от имени $USER_NAME сейчас? [y/N] " setup_ans
  if [[ "$setup_ans" =~ ^[yYдД] ]]; then
    chmod +x "$PROJECT_DIR/setup.sh"
    sudo -u "$USER_NAME" bash -lc "cd '$PROJECT_DIR' && ./setup.sh"
  else
    exit 1
  fi
  if [ ! -x "$PROJECT_DIR/.venv/bin/python" ]; then
    echo "setup.sh не создал .venv — проверь ошибки pip выше."
    exit 1
  fi
fi

chmod +x "$PROJECT_DIR/start.sh" "$PROJECT_DIR/scripts/spider-ap.sh"

echo "==> Группы i2c, gpio для $USER_NAME ..."
usermod -aG i2c,gpio "$USER_NAME" 2>/dev/null || true

echo "==> Генерация unit-файлов ..."
for unit in spider spider-ap; do
  sed "s|@USER@|$USER_NAME|g; s|@PROJECT@|$PROJECT_DIR|g" \
    "$PROJECT_DIR/systemd/$unit.service" > "/etc/systemd/system/$unit.service"
done

echo "==> Включение сервисов ..."
systemctl daemon-reload
systemctl enable spider-ap.service spider.service

read -r -p "Запустить сейчас? [y/N] " ans
if [[ "$ans" =~ ^[yYдД] ]]; then
  systemctl start spider-ap.service
  systemctl start spider.service
  systemctl status spider-ap.service --no-pager || true
  systemctl status spider.service --no-pager || true
fi

echo
echo "Готово. После каждой перезагрузки:"
echo "  1. Pi пробует домашний Wi‑Fi (~45 с)"
echo "  2. Если нет сети — поднимает точку доступа (см. config/spider-ap.conf)"
echo "  3. Пульт: http://<IP-Pi>:5000"
echo
echo "Команды:"
echo "  sudo systemctl status spider"
echo "  journalctl -u spider -f"
echo "  journalctl -u spider-ap -f"
