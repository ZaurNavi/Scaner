#!/usr/bin/env python3
"""Модели данных для Unified Device Profile."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

class IdentityState(Enum):
    """Состояние идентификации устройства."""
    RESOLVED = "resolved"
    MERGED = "merged"
    RECOVERED = "recovered"
    TEMPORARY = "temporary"

@dataclass(frozen=True)
class IdentityReference:
    """
    Идентификация устройства (immutable).
    
    Главный объект платформы.
    """
    device_uuid: str
    primary_mac: str = ""
    current_ip: str = ""
    aliases: tuple = ()  # tuple для immutability
    vendor: str = ""
    hostname: str = ""
    device_type: str = ""
    identity_state: IdentityState = IdentityState.TEMPORARY

@dataclass(frozen=True)
class ProfileSummary:
    """Краткое описание устройства (immutable)."""
    known_since: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    history_depth: int = 0
    sessions: int = 0
    facts: int = 0
    confidence: float = 0.0

@dataclass(frozen=True)
class ProfileStatistics:
    """Статистика профиля (immutable)."""
    facts_total: int = 0
    categories_total: int = 0
    engines_total: int = 0
    highest_confidence: float = 0.0
    average_confidence: float = 0.0
    timeline_events: int = 0
    sessions: int = 0
    history_depth: int = 0
    facts_by_engine: Dict[str, int] = field(default_factory=dict)
    facts_by_category: Dict[str, int] = field(default_factory=dict)
    capabilities_available: int = 0

@dataclass(frozen=True)
class ProfileCoverage:
    """Покрытие профиля (immutable)."""
    timeline: float = 0.0
    metric: float = 0.0
    feature: float = 0.0
    rule: float = 0.0
    fact: float = 0.0
    knowledge: float = 0.0

@dataclass(frozen=True)
class ProfileConfidence:
    """Уверенность профиля (immutable)."""
    overall: float = 0.0
    by_category: Dict[str, float] = field(default_factory=dict)
    by_engine: Dict[str, float] = field(default_factory=dict)

@dataclass(frozen=True)
class ProfileCategories:
    """
    Категории профиля (immutable).
    
    Публичный API — каждое поле соответствует категории.
    """
    presence: Dict[str, Any] = field(default_factory=dict)
    usage: Dict[str, Any] = field(default_factory=dict)
    behaviour: Dict[str, Any] = field(default_factory=dict)
    mobility: Dict[str, Any] = field(default_factory=dict)
