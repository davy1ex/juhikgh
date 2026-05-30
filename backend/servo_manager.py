#!/usr/bin/env python3
"""
Менеджер для управления сервоприводами паука-робота.
Хранит текущие углы в памяти и управляет реальными сервоприводами через PCA9685.
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
    CRAWL_LEG_ORDER,
)


class ServoManager:
    """Управление сервоприводами паука-робота."""

    SWING_DELAYS = (0.05, 0.1, 0.1, 0.1)

    def __init__(self):
        self.angles = {}
        for leg in VALID_LEGS:
            self.angles[leg] = {joint: 90 for joint in VALID_JOINTS}
        self.kit = None
        self._motion_busy = False
        self._init_servos()
        self.current_coxa_angles = COXA_BASE.copy()

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
        return self.kit is not None

    def is_motion_busy(self):
        return self._motion_busy

    def _run_motion(self, action):
        if self._motion_busy:
            return None
        self._motion_busy = True
        try:
            return action()
        finally:
            self._motion_busy = False

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
        base = base_dict[leg]
        sign = 1 if (leg in ['FL', 'BR']) == (direction == 'up') else -1
        return self._clamp_angle(base + sign * offset)

    def _swing_leg(self, leg, tibia_angles, coxa_target, femur_up_offset, femur_down_offset, base_dict,
                   return_coxa=None, return_femur=None, return_tibia=None, delays=SWING_DELAYS):
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

    def _body_push_coxa(self, tibia_angles, coxa_start, coxa_end, steps=10, tibia_delay=0.05, step_delay=0.02):
        for leg in VALID_LEGS:
            self._move_servo_fast(leg, 'tibia', tibia_angles[leg])
        time.sleep(tibia_delay)

        start_angles = {leg: coxa_start[leg] for leg in VALID_LEGS}
        target_angles = {leg: coxa_end[leg] for leg in VALID_LEGS}

        for i in range(steps):
            for leg in VALID_LEGS:
                interp = start_angles[leg] + (target_angles[leg] - start_angles[leg]) * ((i + 1) / steps)
                angle = int(interp)
                if self.kit:
                    ch = LEG_CHANNELS[leg]['coxa']
                    self._setup_servo_pulse_range(ch)
                    self.kit.servo[ch].angle = angle
                self.angles[leg]['coxa'] = angle
            time.sleep(step_delay)

        for leg in VALID_LEGS:
            self.current_coxa_angles[leg] = target_angles[leg]

    def _move_forward_cycle_impl(self):
        try:
            for leg in CRAWL_LEG_ORDER:
                self._swing_leg(
                    leg, TIBIA_BASE, COXA_FORWARD,
                    FEMUR_UP_OFFSET, FEMUR_DOWN_OFFSET, FEMUR_BASE,
                    delays=self.SWING_DELAYS,
                )
                self._body_push_coxa(
                    TIBIA_BASE, self.current_coxa_angles.copy(), COXA_BACKWARD,
                    steps=10, tibia_delay=0.05, step_delay=0.02,
                )
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при движении вперёд: {e}")
            return False

    def move_forward_cycle(self):
        return self._run_motion(self._move_forward_cycle_impl)

    def _move_forward_cycle_low_impl(self):
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
            for leg in CRAWL_LEG_ORDER:
                self._swing_leg(
                    leg, TIBIA_SIT2, COXA_FORWARD,
                    FEMUR_LOW_UP_OFFSET, FEMUR_LOW_DOWN_OFFSET, FEMUR_SIT2,
                    delays=self.SWING_DELAYS,
                )
                self._body_push_coxa(
                    TIBIA_SIT2, self.current_coxa_angles.copy(), COXA_BACKWARD,
                    steps=10, tibia_delay=0.05, step_delay=0.02,
                )
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при движении вперёд (низкая стойка): {e}")
            return False

    def move_forward_cycle_low(self):
        return self._run_motion(self._move_forward_cycle_low_impl)

    def _move_backward_cycle_impl(self):
        try:
            for leg in ['BL', 'FR', 'BR', 'FL']:
                self._swing_leg(
                    leg, TIBIA_BASE, COXA_BACKWARD,
                    FEMUR_UP_OFFSET, FEMUR_DOWN_OFFSET, FEMUR_BASE,
                    delays=self.SWING_DELAYS,
                )
                self._body_push_coxa(TIBIA_BASE, self.current_coxa_angles.copy(), COXA_FORWARD, steps=10)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при движении назад: {e}")
            return False

    def move_backward_cycle(self):
        return self._run_motion(self._move_backward_cycle_impl)

    def _step_right_impl(self):
        try:
            for leg in CRAWL_LEG_ORDER:
                self._swing_leg(
                    leg, TIBIA_BASE, COXA_RIGHT,
                    FEMUR_UP_OFFSET, FEMUR_DOWN_OFFSET, FEMUR_BASE,
                    delays=self.SWING_DELAYS,
                )
                self._body_push_coxa(TIBIA_BASE, self.current_coxa_angles.copy(), COXA_LEFT, steps=10)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при движении вправо: {e}")
            return False

    def step_right(self):
        return self._run_motion(self._step_right_impl)

    def _step_left_impl(self):
        try:
            for leg in CRAWL_LEG_ORDER:
                self._swing_leg(
                    leg, TIBIA_BASE, COXA_LEFT,
                    FEMUR_UP_OFFSET, FEMUR_DOWN_OFFSET, FEMUR_BASE,
                    delays=self.SWING_DELAYS,
                )
                self._body_push_coxa(TIBIA_BASE, self.current_coxa_angles.copy(), COXA_RIGHT, steps=10)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при движении влево: {e}")
            return False

    def step_left(self):
        return self._run_motion(self._step_left_impl)

    def _wave_fl_leg_impl(self, times=3):
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

    def wave_fl_leg(self, times=3):
        return self._run_motion(lambda: self._wave_fl_leg_impl(times))

    def _stand_up_impl(self):
        try:
            for leg in VALID_LEGS:
                self._move_servo_fast(leg, 'coxa', COXA_STANDUP[leg])
                self._move_servo_fast(leg, 'femur', FEMUR_STANDUP[leg])
                self._move_servo_fast(leg, 'tibia', TIBIA_STANDUP[leg])
            self.current_coxa_angles = COXA_STANDUP.copy()
            time.sleep(0.1)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при вставании: {e}")
            return False

    def stand_up(self):
        return self._run_motion(self._stand_up_impl)

    def _sit_down_impl(self):
        try:
            for leg in VALID_LEGS:
                self._move_servo_fast(leg, 'coxa', COXA_SIT2[leg])
                self._move_servo_fast(leg, 'femur', FEMUR_SIT2[leg])
                self._move_servo_fast(leg, 'tibia', TIBIA_SIT2[leg])
            self.current_coxa_angles = COXA_SIT2.copy()
            time.sleep(0.1)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка при приседании: {e}")
            return False

    def sit_down(self):
        return self._run_motion(self._sit_down_impl)

    def push_up(self):
        def _impl():
            if not self._sit_down_impl():
                return False
            time.sleep(0.1)
            return self._stand_up_impl()

        return self._run_motion(_impl)
