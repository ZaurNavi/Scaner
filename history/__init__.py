#!/usr/bin/env python3
"""
History Service — единая точка доступа к историческим данным.
"""

from .service import HistoryService
from .models import (
    SnapshotRecord,
    ObservationRecord,
    EventRecord,
    EvidenceRecord,
    CapabilityRecord,
    DeviceHistory,
)

__all__ = [
    "HistoryService",
    "SnapshotRecord",
    "ObservationRecord",
    "EventRecord",
    "EvidenceRecord",
    "CapabilityRecord",
    "DeviceHistory",
]
