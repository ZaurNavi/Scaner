#!/usr/bin/env python3
"""
Enums для схемы данных.
Никакой бизнес-логики, только строгие типы.
"""

from enum import Enum


class DeviceStatus(str, Enum):
    """Статус устройства в системе."""
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ObservationType(str, Enum):
    """Тип значения в наблюдении (для корректной сериализации/парсинга)."""
    STRING = "STRING"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"


class CollectorStatus(str, Enum):
    """Статус выполнения коллектора."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"
