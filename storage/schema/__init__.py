"""
SISU Core Domain Model v2.0
Чистые структуры данных, независимые от механизма хранения.
"""

from .version import DOMAIN_MODEL_VERSION
from .enums import (
    DeviceStatus, DeviceType, ObservationType, 
    CollectorStatus, ScanStatus, CapabilityType
)
from .source import Source
from .scan import Scan
from .device import Device
from .identity import Identity
from .snapshot import Snapshot
from .observation import Observation
from .evidence import Evidence
from .capability import Capability
from .session import Session
from .collector_log import CollectorLog

__all__ = [
    "DOMAIN_MODEL_VERSION",
    "DeviceStatus", "DeviceType", "ObservationType", 
    "CollectorStatus", "ScanStatus", "CapabilityType",
    "Source",
    "Scan",
    "Device",
    "Identity",
    "Snapshot",
    "Observation",
    "Evidence",
    "Capability",
    "Session",
    "CollectorLog",
]
