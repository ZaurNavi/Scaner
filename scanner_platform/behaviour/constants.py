#!/usr/bin/env python3
"""
Числовые константы для Behaviour Engine.
Все пороги вынесены сюда, Evaluator не содержит числовых значений.
"""

# Версии
ENGINE_VERSION = "1.0.0"
RULES_VERSION = "1.0.0"

# Пороги сессий (в секундах)
SHORT_SESSION_THRESHOLD = 300  # 5 минут
LONG_SESSION_THRESHOLD = 3600  # 1 час

# Пороги мобильности
MOBILE_AP_CHANGES_THRESHOLD = 5
ROAMING_AP_CHANGES_THRESHOLD = 10

# Пороги трафика (в байтах)
LIGHT_USER_TRAFFIC_THRESHOLD = 10 * 1024 * 1024  # 10 MB
HEAVY_USER_TRAFFIC_THRESHOLD = 500 * 1024 * 1024  # 500 MB

# Пороги скорости (в Mbps)
PEAK_SPEED_THRESHOLD = 100  # Mbps

# Пороги активности
IDLE_RATIO_THRESHOLD = 0.8  # 80%
ACTIVE_RATIO_THRESHOLD = 0.2  # 20%

# Пороги дисперсии RSSI/SNR
RSSI_VARIANCE_THRESHOLD = 20  # dB
SNR_VARIANCE_THRESHOLD = 10  # dB

# Максимальный Raw Score для нормализации
MAX_RAW_SCORE = 100
