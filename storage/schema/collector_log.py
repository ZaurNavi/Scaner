#!/usr/bin/env python3
"""
Модель CollectorLog.
История выполнения коллекторов для мониторинга здоровья системы.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .enums import CollectorStatus


@dataclass(frozen=True)
class CollectorLog:
    """
    Лог выполнения одного коллектора для одного устройства.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    collector: str
    mac: str  # Используем MAC, так как device_id может быть еще не известен на этапе сбора
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: datetime | None = None
    elapsed_ms: float = 0.0
    status: CollectorStatus = CollectorStatus.SUCCESS
    error_message: str = ""
