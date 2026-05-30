#!/usr/bin/env python3
"""
Интерактивный тест сервоприводов паука (MG90S + PCA9685).

1. Проверяет I2C и наличие PCA9685 на шине
2. Ставит все серво в нейтраль (90°)
3. По очереди двигает каждый серво и спрашивает, сработал ли он
4. Сохраняет список нерабочих серво в servo_test_report.json

Запуск на Raspberry Pi:
    cd ~/spider
    ./setup.sh                              # один раз
    .venv/bin/python backend/test_servos.py
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from adafruit_extended_bus import ExtendedI2C as I2C
from adafruit_servokit import ServoKit

from spider_config import (
    I2C_BUS,
    LEG_CHANNELS,
    MAX_PULSE,
    MIN_PULSE,
    PCA9685_ADDRESS,
    VALID_JOINTS,
    VALID_LEGS,
)

REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "servo_test_report.json")
NEUTRAL_ANGLE = 90
TEST_OFFSET = 35
MOVE_DELAY = 1.0
RETURN_DELAY = 0.5

JOINT_NAMES_RU = {
    "coxa": "бедро (ближе к корпусу)",
    "femur": "средний сустав",
    "tibia": "голень (дальний)",
}

LEG_NAMES_RU = {
    "FL": "передняя левая",
    "FR": "передняя правая",
    "BL": "задняя левая",
    "BR": "задняя правая",
}


def check_i2c() -> Tuple[bool, List[int], Optional[str]]:
    """Сканирует I2C-шину и проверяет, виден ли PCA9685."""
    try:
        i2c = I2C(I2C_BUS)
        devices = i2c.scan()
    except Exception as exc:
        return False, [], f"Не удалось открыть I2C bus {I2C_BUS}: {exc}"

    if PCA9685_ADDRESS not in devices:
        found = ", ".join(f"0x{d:02x}" for d in devices) or "ничего"
        return False, devices, (
            f"PCA9685 не найден по адресу 0x{PCA9685_ADDRESS:02x}. "
            f"На шине: {found}. Проверь SDA/SCL, питание VCC и общий GND."
        )

    return True, devices, None


def init_servokit() -> ServoKit:
    i2c = I2C(I2C_BUS)
    kit = ServoKit(channels=16, address=PCA9685_ADDRESS, i2c=i2c)
    for leg in VALID_LEGS:
        for joint in VALID_JOINTS:
            channel = LEG_CHANNELS[leg][joint]
            kit.servo[channel].set_pulse_width_range(MIN_PULSE, MAX_PULSE)
    return kit


def move_servo(kit: ServoKit, channel: int, angle: float) -> None:
    kit.servo[channel].angle = angle
    time.sleep(MOVE_DELAY)


def release_servo(kit: ServoKit, channel: int) -> None:
    kit.servo[channel].angle = None
    time.sleep(RETURN_DELAY)


def servo_label(leg: str, joint: str) -> str:
    channel = LEG_CHANNELS[leg][joint]
    return (
        f"{leg}-{joint} (канал {channel}, "
        f"{LEG_NAMES_RU[leg]}, {JOINT_NAMES_RU[joint]})"
    )


def ask_yes_no(prompt: str) -> bool:
    while True:
        answer = input(f"{prompt} [y/n]: ").strip().lower()
        if answer in ("y", "yes", "д", "да"):
            return True
        if answer in ("n", "no", "н", "нет"):
            return False
        print("Ответь y/да или n/нет.")


def save_report(working: list[dict], failed: list[dict], i2c_devices: list[int]) -> str:
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "i2c_bus": I2C_BUS,
        "pca9685_address": f"0x{PCA9685_ADDRESS:02x}",
        "i2c_devices_found": [f"0x{d:02x}" for d in i2c_devices],
        "working": working,
        "failed": failed,
        "summary": {
            "total": len(working) + len(failed),
            "working_count": len(working),
            "failed_count": len(failed),
        },
    }
    with open(REPORT_FILE, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    return REPORT_FILE


def print_header() -> None:
    print()
    print("=" * 60)
    print("  ТЕСТ СЕРВОПРИВОДОВ QUADRO SPIDER (MG90S + PCA9685)")
    print("=" * 60)
    print()
    print("Перед тестом:")
    print("  • Питание V+ на PCA9685 включено (18650 → XLA → V+)")
    print("  • Общий GND между Pi, PCA9685 и блоком питания")
    print("  • Серво подключены по LEG_CHANNELS из spider_config.py")
    print()
    print("Каналы:")
    for leg in VALID_LEGS:
        channels = ", ".join(
            f"{joint}={LEG_CHANNELS[leg][joint]}" for joint in VALID_JOINTS
        )
        print(f"  {leg}: {channels}")
    print()


def main() -> int:
    print_header()

    print(f"Шаг 1/3: проверка I2C (bus {I2C_BUS}, адрес 0x{PCA9685_ADDRESS:02x})...")
    ok, devices, error = check_i2c()
    if not ok:
        print(f"❌ {error}")
        print()
        print("Подсказки:")
        print("  sudo raspi-config  → Interface Options → I2C → Enable")
        print("  sudo i2cdetect -y 1")
        return 1

    found = ", ".join(f"0x{d:02x}" for d in devices)
    print(f"✅ I2C OK. Устройства на шине: {found}")
    print(f"✅ PCA9685 найден по адресу 0x{PCA9685_ADDRESS:02x}")
    print()

    print("Шаг 2/3: инициализация ServoKit...")
    try:
        kit = init_servokit()
    except Exception as exc:
        print(f"❌ ServoKit не инициализировался: {exc}")
        return 1
    print("✅ ServoKit готов")
    print()

    print("Шаг 3/3: тест каждого серво по очереди")
    print(f"Нейтраль: {NEUTRAL_ANGLE}°, тестовый ход: ±{TEST_OFFSET}°")
    print("Смотри на серво и отвечай, двинулся ли он.")
    print()

    input("Нажми Enter, чтобы поставить все серво в нейтраль и начать...")

    for leg in VALID_LEGS:
        for joint in VALID_JOINTS:
            channel = LEG_CHANNELS[leg][joint]
            move_servo(kit, channel, NEUTRAL_ANGLE)
            release_servo(kit, channel)

    working: List[dict] = []
    failed: List[dict] = []

    total = len(VALID_LEGS) * len(VALID_JOINTS)
    index = 0

    for leg in VALID_LEGS:
        for joint in VALID_JOINTS:
            index += 1
            channel = LEG_CHANNELS[leg][joint]
            label = servo_label(leg, joint)

            print("-" * 60)
            print(f"[{index}/{total}] Тест: {label}")

            test_angle = min(NEUTRAL_ANGLE + TEST_OFFSET, 180)
            move_servo(kit, channel, test_angle)

            moved = ask_yes_no(f"  {label} — двинулся?")

            move_servo(kit, channel, NEUTRAL_ANGLE)
            release_servo(kit, channel)

            entry = {
                "leg": leg,
                "joint": joint,
                "channel": channel,
                "label": label,
            }

            if moved:
                working.append(entry)
                print("  ✅ OK")
            else:
                failed.append(entry)
                print("  ❌ Запомнил как нерабочий")

            print()

    report_path = save_report(working, failed, devices)

    print("=" * 60)
    print("  ИТОГ")
    print("=" * 60)
    print(f"Рабочих: {len(working)}/{total}")
    print(f"Не работают: {len(failed)}/{total}")

    if failed:
        print()
        print("Проблемные серво:")
        for item in failed:
            print(f"  • {item['label']}")
        print()
        print("Проверь для каждого:")
        print("  1. Провод сигнала в правильный канал PCA9685")
        print("  2. Контакт в разъёме серво (часто плохой на AliExpress)")
        print("  3. Хватает ли тока на V+ (18650 → XLA → PCA9685 V+)")
    else:
        print()
        print("🎉 Все серво ответили. Можно переходить к калибровке углов.")

    print()
    print(f"Отчёт сохранён: {report_path}")
    return 0 if not failed else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nТест прерван. Частичный отчёт не сохранён.")
        sys.exit(130)
