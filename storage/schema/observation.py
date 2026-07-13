#!/usr/bin/env python3
"""
Модель Observation.
Атомарный факт, привязанный к Snapshot.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .enums import ObservationType
from .source import Source


@dataclass(frozen=True)
class Observation:
    """
    Один факт об устройстве в рамках конкретного Snapshot.
    Пример: Source=TTL, key="ttl", value="64", confidence=40
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snapshot_id: str
    source: Source
    key: str
    value: str  # Храним как строку для универсальности, тип указан в obs_type
    obs_type: ObservationType = ObservationType.STRING
    confidence: int = 0
