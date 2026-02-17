#!/usr/bin/env python3
"""
Менеджер для управления сервоприводами паука-робота.
Хранит текущие углы в памяти и управляет реальными сервоприводами через PCA9685.
Используется только API, вызываемое из frontend (index.html / app.js).
"""

import time
from adafruit_servokit import ServoKit
from adafruit_extended_bus import ExtendedI2C as I2C

from spider_config import (
    I2C_BUS, PCA9685_ADDRESS, MIN_PULSE, MAX_PULSE,
    LEG_CHANNELS, VALID_LEGS, VALID_JOINTS,
    COXA_BASE, FEMUR_BASE, TIBIA_BASE,
    COXA_STANDUP, FEMUR_STANDUP, TIBIA_STANDUP,
    COXA_SIT2, FEMUR_SIT2, TIBIA_SIT2,
    FEMUR_UP_OFFSET, FEMUR_DOWN_OFFSET, FEMUR_LOW_UP_OFFSET, FEMUR_LOW_DOWN_OFFSET,
    COXA_FORWARD, COXA_BACKWARD, COXA_LEFT, COXA_RIGHT,
    FEMUR_SWING_OFFSET,
)


class ServoManager:
    """Управление сервоприводами паука-робота (только API для frontend)."""

    def __init__(self):
        self.angles = {}
        for leg in VALID_LEGS:
            self.angles[leg] = {joint: 90 for joint in VALID_JOINTS}
        self.kit = None
        self._init_servos()
        self.current_coxa_angles = COXA_BACKWARD.copy()

    def _init_servos(self):
        try:
            i2c = I2C(I2C_BUS)
            self.kit = ServoKit(channels=16, address=PCA9685_ADDRESS, i2c=i2c)
            for leg in VALID_LEGS:
                for joint in VALID_JOINTS:
                    self._setup_servo_pulse_range(LEG_CHANNELS[leg][joint])
            print(f"✅ ServoManager инициализирован: {len(VALID_LEGS) * len(VALID_JOINTS)} сервоприводов")
        except Exception as e:
            print(f"⚠️ Предупреждение: не удалось инициализировать сервоприводы: {e}")
            print("   Работаем в режиме без железа (только хранение углов в памяти)")
            self.kit = None

    def _setup_servo_pulse_range(self, channel):
        if self.kit:
            self.kit.servo[channel].set_pulse_width_range(MIN_PULSE, MAX_PULSE)

    def is_i2c_connected(self):
        """Проверка: подключен ли PCA9685 по I2C."""
        return self.kit is not None

    def get_all_angles(self):
        return self.angles.copy()

    def set_angle(self, leg, joint, angle):
        if leg not in VALID_LEGS or joint not in VALID_JOINTS:
            return False
        try:
            angle = float(angle)
            if angle < 0 or angle > 180:
                return False
        except (ValueError, TypeError):
            return False
        if self.kit:
            try:
                ch = LEG_CHANNELS[leg][joint]
                self._setup_servo_pulse_range(ch)
                self.kit.servo[ch].angle = angle
                time.sleep(0.3)
                self.kit.servo[ch].angle = None
            except Exception as e:
                print(f"⚠️ Ошибка при установке угла {leg} {joint}: {e}")
        self.angles[leg][joint] = angle
        if joint == 'coxa':
            self.current_coxa_angles[leg] = angle
        return True

    def _move_servo_fast(self, leg, joint, angle):
        if not self.kit:
            self.angles[leg][joint] = angle
            if joint == 'coxa':
                self.current_coxa_angles[leg] = angle
            return
        try:
            ch = LEG_CHANNELS[leg][joint]
            self._setup_servo_pulse_range(ch)
            self.kit.servo[ch].angle = angle
            self.angles[leg][joint] = angle
            if joint == 'coxa':
                self.current_coxa_angles[leg] = angle
        except Exception as e:
            print(f"⚠️ Ошибка при движении {leg} {joint}: {e}")

    def _clamp_angle(self, angle):
        return max(0, min(180, angle))

    def _get_femur_offset_angle(self, leg, base_dict, offset, direction='up'):
        """direction: 'up' или 'down'. FL/BR: up=+, down=-; FR/BL: наоборот."""
        base = base_dict[leg]
        sign = 1 if (leg in ['FL', 'BR']) == (direction == 'up') else -1
        return self._clamp_angle(base + sign * offset)

    # --- Позы (используются кнопками в index.html) ---
    def push_up(self):
        self.sit_down()
        time.sleep(0.1)
        self.stand_up()

    SWING_DELAY = 0.1
    STEP_DELAY = 0.4

    def _swing_leg(self, leg, tibia_angles, coxa_target, femur_up_offset, femur_down_offset, base_dict,
                   return_coxa=None, return_femur=None, return_tibia=None, delays=(0.05, 0.1, 0.1, 0.1)):
        """Универсальный swing: tibia -> femur_up -> coxa -> femur_down. Опционально: return к base."""
        d0, d1, d2, d3 = delays
        self._move_servo_fast(leg, 'tibia', tibia_angles[leg])
        time.sleep(d0)
        self._move_servo_fast(leg, 'femur', self._get_femur_offset_angle(leg, base_dict, femur_up_offset, 'up'))
        time.sleep(d1)
        self._move_servo_fast(leg, 'coxa', coxa_target[leg])
        self.current_coxa_angles[leg] = coxa_target[leg]
        time.sleep(d2)
        self._move_servo_fast(leg, 'femur', self._get_femur_offset_angle(leg, base_dict, femur_down_offset, 'down'))
        time.sleep(d3)
        if return_coxa is not None and return_femur is not None and return_tibia is not None:
            self._move_servo_fast(leg, 'coxa', return_coxa[leg])
            time.sleep(d0)
            self._move_servo_fast(leg, 'femur', return_femur[leg])
            time.sleep(d0)
            self._move_servo_fast(leg, 'tibia', return_tibia[leg])
            time.sleep(d0)
            self.current_coxa_angles[leg] = return_coxa[leg]

    def move_forward_cycle(self):
        try:
            d = 0.1
            for leg in ['FL', 'BR', 'FR', 'BL']:
                self._move_servo_fast(leg, 'tibia', TIBIA_BASE[leg])
                if leg in ("FL", "BR"):
                    self._move_servo_fast(leg, 'femur', FEMUR_BASE[leg] + FEMUR_SWING_OFFSET)
                else:
                    self._move_servo_fast(leg, 'femur', FEMUR_BASE[leg] - FEMUR_SWING_OFFSET)
                self._move_servo_fast(leg, 'tibia', TIBIA_BASE[leg])
                self._move_servo_fast(leg, 'coxa', COXA_FORWARD[leg])
                self.current_coxa_angles[leg] = COXA_FORWARD[leg]
                self._move_servo_fast(leg, 'tibia', TIBIA_BASE[leg])
                time.sleep(d)
                if leg in ("FL", "BR"):
                    self._move_servo_fast(leg, 'femur', FEMUR_BASE[leg] - FEMUR_SWING_OFFSET)
                else:
                    self._move_servo_fast(leg, 'femur', FEMUR_BASE[leg] + FEMUR_SWING_OFFSET)
                self._move_servo_fast(leg, 'tibia', TIBIA_BASE[leg])
                time.sleep(d)
                self._move_servo_fast(leg, 'coxa', COXA_BASE[leg])
                time.sleep(d)
                self._move_servo_fast(leg, 'femur', FEMUR_BASE[leg])
                self._move_servo_fast(leg, 'tibia', TIBIA_BASE[leg])
                time.sleep(d)
                self.current_coxa_angles[leg] = COXA_BASE[leg]
                self._body_push_coxa(TIBIA_BASE, COXA_BASE, COXA_BACKWARD, steps=5, tibia_delay=0.25, step_delay=0.01)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при движении вперёд: {e}")
            return False

    def _body_push_coxa(self, tibia_angles, coxa_start, coxa_end, steps=5, tibia_delay=0.05, step_delay=0.02):
        """Универсальный body push: tibia -> интерполяция coxa от start к end."""
        for leg in VALID_LEGS:
            self._move_servo_fast(leg, 'tibia', tibia_angles[leg])
        time.sleep(tibia_delay)
        target_angles = {}
        for leg in VALID_LEGS:
            start, end = coxa_start[leg], coxa_end[leg]
            inc = (end - start) / 4.0
            new_angle = coxa_start[leg] + inc
            new_angle = min(new_angle, end) if start < end else max(new_angle, end)
            target_angles[leg] = new_angle
        start_angles = {leg: coxa_start[leg] for leg in VALID_LEGS}
        for i in range(steps):
            for leg in VALID_LEGS:
                interp = start_angles[leg] + (target_angles[leg] - start_angles[leg]) * ((i + 1) / steps)
                if self.kit:
                    ch = LEG_CHANNELS[leg]['coxa']
                    self._setup_servo_pulse_range(ch)
                    self.kit.servo[ch].angle = int(interp)
                self.angles[leg]['coxa'] = int(interp)
            time.sleep(step_delay)
        for leg in target_angles:
            self.current_coxa_angles[leg] = target_angles[leg]

    def move_forward_cycle_low(self):
        try:
            for leg in VALID_LEGS:
                self._move_servo_fast(leg, 'coxa', COXA_SIT2[leg])
                time.sleep(0.04)
                self._move_servo_fast(leg, 'femur', FEMUR_SIT2[leg])
                time.sleep(0.04)
                self._move_servo_fast(leg, 'tibia', TIBIA_SIT2[leg])
                time.sleep(0.04)
                self.current_coxa_angles[leg] = COXA_SIT2[leg]
            time.sleep(0.2)
            for leg in ['FL', 'BR', 'FR', 'BL']:
                self._swing_leg(leg, TIBIA_SIT2, COXA_FORWARD, FEMUR_LOW_UP_OFFSET, FEMUR_LOW_DOWN_OFFSET, FEMUR_SIT2,
                               delays=(0.05, 0.1, 0.1, 0.1))
                self._body_push_coxa(TIBIA_SIT2, self.current_coxa_angles.copy(), COXA_BACKWARD, steps=10, tibia_delay=0.05, step_delay=0.02)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при движении вперёд (низкая стойка): {e}")
            return False

    # --- Походка назад ---
    def _swing_leg_backward(self, leg):
        self._move_servo_fast(leg, 'tibia', TIBIA_BASE[leg])
        time.sleep(0.05)
        self._move_servo_fast(leg, 'femur', self._get_femur_offset_angle(leg, FEMUR_BASE, FEMUR_UP_OFFSET, 'up'))
        time.sleep(0.1)
        self._move_servo_fast(leg, 'coxa', COXA_BACKWARD[leg])
        self.current_coxa_angles[leg] = COXA_BACKWARD[leg]
        time.sleep(0.1)
        self._move_servo_fast(leg, 'femur', self._get_femur_offset_angle(leg, FEMUR_BASE, FEMUR_DOWN_OFFSET, 'down'))
        time.sleep(0.1)

    def move_backward_cycle(self):
        try:
            for leg in ['BL', 'FR', 'BR', 'FL']:
                self._swing_leg(leg, TIBIA_BASE, COXA_BACKWARD, FEMUR_UP_OFFSET, FEMUR_DOWN_OFFSET, FEMUR_BASE,
                               delays=(0.05, 0.1, 0.1, 0.1))
                self._body_push_coxa(TIBIA_BASE, self.current_coxa_angles.copy(), COXA_FORWARD, steps=10)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при движении назад: {e}")
            return False

    # --- Шаг вправо ---
    def _swing_leg_right(self, leg):
        self._move_servo_fast(leg, 'tibia', TIBIA_BASE[leg])
        time.sleep(0.05)
        self._move_servo_fast(leg, 'femur', self._get_femur_offset_angle(leg, FEMUR_BASE, FEMUR_UP_OFFSET, 'up'))
        time.sleep(0.1)
        self._move_servo_fast(leg, 'coxa', COXA_RIGHT[leg])
        self.current_coxa_angles[leg] = COXA_RIGHT[leg]
        time.sleep(0.1)
        self._move_servo_fast(leg, 'femur', self._get_femur_offset_angle(leg, FEMUR_BASE, FEMUR_DOWN_OFFSET, 'down'))
        time.sleep(0.1)

    def step_right(self):
        try:
            for leg in ['FL', 'BR', 'FR', 'BL']:
                self._swing_leg(leg, TIBIA_BASE, COXA_RIGHT, FEMUR_UP_OFFSET, FEMUR_DOWN_OFFSET, FEMUR_BASE,
                               delays=(0.05, 0.1, 0.1, 0.1))
                self._body_push_coxa(TIBIA_BASE, self.current_coxa_angles.copy(), COXA_LEFT, steps=10)
            
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при движении вправо: {e}")
            return False

    def step_left(self):
        """Шаг влево — обратная логика step_right."""
        try:
            for leg in ['FL', 'BR', 'FR', 'BL']:
                self._swing_leg(leg, TIBIA_BASE, COXA_LEFT, FEMUR_UP_OFFSET, FEMUR_DOWN_OFFSET, FEMUR_BASE,
                               delays=(0.05, 0.1, 0.1, 0.1))
                self._body_push_coxa(TIBIA_BASE, self.current_coxa_angles.copy(), COXA_RIGHT, steps=10)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при движении влево: {e}")
            return False

    def wave_fl_leg(self, times=3):
        """Помахать передней левой лапкой (FL) несколько раз."""
        try:
            for _ in range(times):
                self._move_servo_fast('FL', 'femur', FEMUR_BASE['FL'] + 20)
                time.sleep(0.2)
                self._move_servo_fast('FL', 'femur', FEMUR_BASE['FL'])
                time.sleep(0.2)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при махании лапкой FL: {e}")
            return False
    
    
    def stand_up(self):
        """Встать — все ноги одновременно в базовое положение."""
        try:
            for leg in VALID_LEGS:
                self._move_servo_fast(leg, 'coxa', COXA_STANDUP[leg])
                self._move_servo_fast(leg, 'femur', FEMUR_STANDUP[leg])
                self._move_servo_fast(leg, 'tibia', TIBIA_STANDUP[leg])
            time.sleep(0.1)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при вставании: {e}")
            return False

    def sit_down(self):
        """Сесть — все ноги одновременно в просевшее положение (SIT2)."""
        try:
            for leg in VALID_LEGS:
                self._move_servo_fast(leg, 'coxa', COXA_SIT2[leg])
                self._move_servo_fast(leg, 'femur', FEMUR_SIT2[leg])
                self._move_servo_fast(leg, 'tibia', TIBIA_SIT2[leg])
            time.sleep(0.1)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при приседании: {e}")
            return False

