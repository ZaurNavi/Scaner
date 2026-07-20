#!/usr/bin/env python3
"""
Models — Observation и UnifiedObservation.
ES-1.8.1: Единый формат наблюдений.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class ObservationCategory(Enum):
    """
    Категории наблюдений.
    
    ES-1.8.1: Строки запрещены, только Enum.
    """
    IDENTITY = "identity"
    NETWORK = "network"
    SERVICE = "service"
    TRANSPORT = "transport"
    SECURITY = "security"
    APPLICATION = "application"
    TIMING = "timing"
    VENDOR = "vendor"


@dataclass
class Observation:
    """
    Сырая запись наблюдения от Collector.
    
    ES-1.8.1: Минимальная модель с observation_id.
    """
    observation_id: str
    collector_id: str
    protocol: str
    transport: str
    device_id: str  # IP или MAC
    attribute: str
    value: Any
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @staticmethod
    def generate_id(
        collector_id: str,
        device_id: str,
        attribute: str,
        value: Any,
        timestamp: datetime
    ) -> str:
        """
        Генерирует стабильный observation_id через SHA256.
        
        ES-1.8.1: Используется для дедупликации, истории, ссылок.
        """
        content = f"{collector_id}:{device_id}:{attribute}:{value}:{timestamp.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass(frozen=True)
class UnifiedObservation:
    """
    Нормализованное наблюдение.
    
    ES-1.8.1: Immutable (frozen=True).
    После создания менять ничего нельзя.
    
    Независимость:
    - Не содержит Profile, Session, Knowledge, Risk, History, Events, Device State
    """
    observation_id: str
    collector_id: str
    protocol: str
    transport: str
    category: ObservationCategory
    attribute: str
    normalized_value: Any
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_immutable(self) -> bool:
        """UnifiedObservation действительно immutable."""
        return True
