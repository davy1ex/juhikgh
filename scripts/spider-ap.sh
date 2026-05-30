#!/bin/bash
# Поднимает Wi‑Fi точку доступа, если Pi не получил IP по wlan0 (нет домашней сети).
# Нужен NetworkManager (Raspberry Pi OS Bookworm). Запускается через systemd до пульта.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONF="$PROJECT_DIR/config/spider-ap.conf"
HOTSPOT_CON="SpiderHotspot"

if [ -f "$CONF" ]; then
  # shellcheck source=/dev/null
  source "$CONF"
fi

SSID="${SPIDER_AP_SSID:-Spider-Pi}"
PASSWORD="${SPIDER_AP_PASSWORD:-spider1234}"
WAIT_SEC="${SPIDER_AP_WAIT_SEC:-45}"

log() { echo "[spider-ap] $*"; }

has_wlan_ip() {
  ip -4 addr show wlan0 2>/dev/null | grep -q 'inet '
}

wait_for_home_wifi() {
  log "Жду домашний Wi‑Fi до ${WAIT_SEC} с..."
  for _ in $(seq 1 "$WAIT_SEC"); do
    if has_wlan_ip; then
      log "wlan0 получил IP — точка доступа не нужна."
      return 0
    fi
    sleep 1
  done
  return 1
}

start_hotspot() {
  if ! command -v nmcli >/dev/null 2>&1; then
    log "nmcli не найден. Установи NetworkManager или см. README (hostapd)."
    exit 1
  fi

  if nmcli -t -f NAME con show 2>/dev/null | grep -qx "$HOTSPOT_CON"; then
    log "Hotspot уже настроен, поднимаю $HOTSPOT_CON ..."
    nmcli con up "$HOTSPOT_CON"
  else
    log "Поднимаю точку доступа: SSID=$SSID"
    nmcli dev wifi hotspot ifname wlan0 con-name "$HOTSPOT_CON" ssid "$SSID" password "$PASSWORD"
  fi

  AP_IP="$(ip -4 addr show wlan0 2>/dev/null | awk '/inet / {print $2}' | head -1 | cut -d/ -f1)"
  log "Готово. Подключись к Wi‑Fi «$SSID», пароль: $PASSWORD"
  SSH_USER="${SPIDER_USER:-pi}"
  log "Пульт: http://${AP_IP:-10.42.0.1}:5000   SSH: ssh ${SSH_USER}@${AP_IP:-10.42.0.1}"
}

stop_hotspot() {
  if command -v nmcli >/dev/null 2>&1; then
    nmcli con down "$HOTSPOT_CON" 2>/dev/null || true
  fi
}

case "${1:-start}" in
  start)
    if wait_for_home_wifi; then
      exit 0
    fi
    start_hotspot
    ;;
  stop)
    stop_hotspot
    ;;
  *)
    echo "Usage: $0 {start|stop}"
    exit 1
    ;;
esac
