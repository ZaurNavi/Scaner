#!/usr/bin/env python3
"""Константы и версии для Mobility Engine."""

ENGINE_VERSION = "1.0.0"
RULES_VERSION = "1.0.0"

# Пороги для правил (примеры)
ROAMING_RATE_THRESHOLD = 3  # смен AP за сессию
STATIONARY_RATIO_THRESHOLD = 0.8  # 80% времени на одной AP
MOVEMENT_RADIUS_THRESHOLD = 2  # количество уникальных AP
