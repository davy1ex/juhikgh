"""
Конфигурация углов и каналов для паука-робота.
Подогнано под калибровку PCA9685.
"""

# I2C и PCA9685
I2C_BUS = 1
PCA9685_ADDRESS = 0x40
MIN_PULSE = 500
MAX_PULSE = 2500

# Маппинг ног и суставов к каналам PCA9685
LEG_CHANNELS = {
    'FL': {'coxa': 0, 'femur': 1, 'tibia': 2},
    'FR': {'coxa': 3, 'femur': 4, 'tibia': 5},
    'BL': {'coxa': 6, 'femur': 7, 'tibia': 8},
    'BR': {'coxa': 9, 'femur': 10, 'tibia': 11}
}
VALID_LEGS = ['FL', 'FR', 'BL', 'BR']
VALID_JOINTS = ['coxa', 'femur', 'tibia']

# Базовая стойка — походка (diagonal crawl), «Встать в базовое»
COXA_BASE = {'FL': 60, 'FR': 120, 'BL': 120, 'BR': 60}
FEMUR_BASE = {'FL': 140, 'FR': 40, 'BL': 40, 'BR': 140}
TIBIA_BASE = {'FL': 130, 'FR': 40, 'BL': 40, 'BR': 130}

# Высокая стойка — «Встать вверх», отжимание
COXA_STANDUP = {'FL': 60, 'FR': 120, 'BL': 120, 'BR': 60}
FEMUR_STANDUP = {'FL': 90, 'FR': 90, 'BL': 90, 'BR': 90}
TIBIA_STANDUP = {'FL': 90, 'FR': 90, 'BL': 90, 'BR': 90}

# Сесть (просевшее положение)
COXA_SIT2 = {'FL': 60, 'FR': 120, 'BL': 120, 'BR': 60}
FEMUR_SIT2 = {'FL': 150, 'FR': 30, 'BL': 30, 'BR': 150}
TIBIA_SIT2 = {'FL': 180, 'FR': 30, 'BL': 30, 'BR': 180}

# Оффсеты для движения
FEMUR_UP_OFFSET = 60
FEMUR_DOWN_OFFSET = 30
FEMUR_LOW_UP_OFFSET = 30
FEMUR_LOW_DOWN_OFFSET = 10

# Coxa для походки вперёд/назад
COXA_FORWARD = {'FL': 30, 'FR': 160, 'BL': 60, 'BR': 160}
COXA_BACKWARD = {'FL': 80, 'FR': 100, 'BL': 140, 'BR': 40}

# Coxa для бокового шага
COXA_RIGHT = {'FL': 100, 'FR': 80, 'BL': 100, 'BR': 80}
COXA_LEFT = {'FL': 50, 'FR': 130, 'BL': 130, 'BR': 50}

# Порядок ног для diagonal crawl (Hackster-порядок)
CRAWL_LEG_ORDER = ['FL', 'BR', 'FR', 'BL']
CRAWL_LEG_ORDER_BACKWARD = list(reversed(CRAWL_LEG_ORDER))  # BL → FR → BR → FL
