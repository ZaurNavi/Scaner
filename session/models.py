#!/usr/bin/env python3
"""
Модели данных для Session Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class SessionStatus(Enum):
    """Статус сессии."""
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class SessionEndReason(Enum):
    """Причина завершения сессии."""
    TIMEOUT = "TIMEOUT"
    PROGRAM_SHUTDOWN = "PROGRAM_SHUTDOWN"
    UNKNOWN = "UNKNOWN"


@dataclass
class Session:
    """
    Непрерывное присутствие устройства в сети.
    Неизменяема после получения статуса ENDED.
    """
    # 1. Поля БЕЗ значений по умолчанию (должны идти первыми!)
    id: str
    device_id: str
    start_time: datetime
    last_seen: datetime
    
    # 2. Поля СО значениями по умолчанию (должны идти после)
    schema_version: int = 1
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # в секундах
    
    status: SessionStatus = SessionStatus.ACTIVE
    end_reason: Optional[SessionEndReason] = None
    
    ip_history: List[str] = field(default_factory=list)
    hostname_history: List[str] = field(default_factory=list)
    snapshots_count: int = 0
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
