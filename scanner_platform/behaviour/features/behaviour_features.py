#!/usr/bin/env python3
"""Feature Builders для Behaviour Engine."""
from typing import Dict, Any

def build_regular_schedule(metrics: Dict[str, Any]) -> bool:
    """Устройство появляется по регулярному расписанию."""
    daily = metrics.get("daily_presence", 0.0)
    weekday = metrics.get("weekday_ratio", 0.0)
    office = metrics.get("office_hours_activity", 0.0)
    
    # Регулярное расписание: высокая дневная активность + будни + рабочие часы
    return daily > 0.5 and weekday > 0.7 and office > 0.6

def build_night_user(metrics: Dict[str, Any]) -> bool:
    """Устройство активно ночью."""
    night = metrics.get("night_activity", 0.0)
    return night > 0.3

def build_weekend_device(metrics: Dict[str, Any]) -> bool:
    """Устройство активно в выходные."""
    weekend = metrics.get("weekend_presence", 0.0)
    return weekend > 0.4

def build_office_pattern(metrics: Dict[str, Any]) -> bool:
    """Паттерн офисного устройства."""
    office = metrics.get("office_hours_activity", 0.0)
    weekday = metrics.get("weekday_ratio", 0.0)
    return office > 0.6 and weekday > 0.7

def build_home_pattern(metrics: Dict[str, Any]) -> bool:
    """Паттерн домашнего устройства."""
    weekend = metrics.get("weekend_presence", 0.0)
    night = metrics.get("night_activity", 0.0)
    return weekend > 0.3 and night > 0.2

def build_frequent_short_sessions(metrics: Dict[str, Any]) -> bool:
    """Частые короткие сессии."""
    freq = metrics.get("appearance_frequency", 0)
    idle = metrics.get("idle_duration", 0.0)
    return freq > 10 and idle > 0.7

def build_long_sessions(metrics: Dict[str, Any]) -> bool:
    """Длинные сессии."""
    online = metrics.get("online_duration", 0.0)
    return online > 3600  # более 1 часа

def build_irregular_usage(metrics: Dict[str, Any]) -> bool:
    """Нерегулярное использование."""
    daily = metrics.get("daily_presence", 0.0)
    weekly = metrics.get("weekly_presence", 0.0)
    return daily < 0.3 and weekly > 0.2

def build_rare_device(metrics: Dict[str, Any]) -> bool:
    """Редко появляющееся устройство."""
    freq = metrics.get("appearance_frequency", 0)
    daily = metrics.get("daily_presence", 0.0)
    return freq < 3 and daily < 0.1

def build_always_online(metrics: Dict[str, Any]) -> bool:
    """Постоянно онлайн."""
    daily = metrics.get("daily_presence", 0.0)
    idle = metrics.get("idle_duration", 0.0)
    return daily > 0.9 and idle < 0.2

def build_frequently_returning(metrics: Dict[str, Any]) -> bool:
    """Часто возвращающееся устройство."""
    freq = metrics.get("appearance_frequency", 0)
    weekly = metrics.get("weekly_presence", 0.0)
    return freq > 5 and weekly > 0.5
