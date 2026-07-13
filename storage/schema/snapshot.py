#!/usr/bin/env python3
"""
Модель Snapshot.
Снимок состояния устройства в конкретный момент времени.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass(frozen=True)
class Snapshot:
    """
    Снимок состояния устройства.
    Отвечает на вопрос: "Что было известно об устройстве в этот момент?"
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    ip: str
    hostname: str = ""
    vendor: str = ""
    model: str = ""
    os: str = ""
    device_type: str = ""
    confidence: int = 0
