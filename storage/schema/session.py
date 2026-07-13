#!/usr/bin/env python3
"""
Модель Session.
Информация о сетевой активности устройства за период.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass(frozen=True)
class Session:
    """
    Сетевая сессия устройства.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: datetime | None = None
    duration: float = 0.0  # в секундах
    traffic_rx: int = 0    # байты
    traffic_tx: int = 0    # байты
