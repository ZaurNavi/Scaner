#!/usr/bin/env python3
"""
Категории поведения и статусы для Behaviour Engine.
"""

from enum import Enum


class BehaviourCategory(Enum):
    """Категории поведения устройства."""
    # Активность
    NORMAL_USER = "normal_user"
    LIGHT_USER = "light_user"
    HEAVY_USER = "heavy_user"
    
    # Мобильность
    MOBILE = "mobile"
    STATIONARY = "stationary"
    ROAMING = "roaming"
    
    # Сессии
    SHORT_SESSION = "short_session"
    LONG_SESSION = "long_session"
    
    # Состояние
    ACTIVE = "active"
    IDLE = "idle"
    PERIODIC = "periodic"
    
    # Время
    DAY_ACTIVE = "day_active"
    NIGHT_ACTIVE = "night_active"
    
    # Неизвестно
    UNKNOWN = "unknown"


class BehaviourStatus(Enum):
    """Статус поведенческого факта."""
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CONFIRMED = "CONFIRMED"
