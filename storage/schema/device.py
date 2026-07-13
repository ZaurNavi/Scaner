#!/usr/bin/env python3
"""
Модель Device.
Главная карточка устройства.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .enums import DeviceStatus


@dataclass(frozen=True)
class Device:
    """
    Главная карточка устройства.
    Существует всегда, никогда не удаляется (только ARCHIVED).
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mac: str
    created_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    status: DeviceStatus = DeviceStatus.ACTIVE
