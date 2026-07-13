"""
Схема данных (Data Model).
Чистые структуры данных, независимые от механизма хранения.
"""

from .enums import DeviceStatus, ObservationType, CollectorStatus
from .source import Source
from .device import Device
from .snapshot import Snapshot
from .observation import Observation
from .session import Session
from .collector_log import CollectorLog

__all__ = [
    "DeviceStatus",
    "ObservationType",
    "CollectorStatus",
    "Source",
    "Device",
    "Snapshot",
    "Observation",
    "Session",
    "CollectorLog",
]
