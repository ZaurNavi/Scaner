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
    # Идентификаторы
    id: str
    device_id: str
    schema_version: int = 1
    
    # Временные характеристики
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # в секундах
    
    # Состояние
    status: SessionStatus = SessionStatus.ACTIVE
    end_reason: Optional[SessionEndReason] = None
    
    # История
    ip_history: List[str] = field(default_factory=list)
    hostname_history: List[str] = field(default_factory=list)
    
    # Метаданные
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
