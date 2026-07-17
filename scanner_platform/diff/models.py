#!/usr/bin/env python3
"""Immutable модели данных для ProfileDiff."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Tuple
from types import MappingProxyType
from enum import Enum
import json

from .enums import ChangeType, CapabilityState

@dataclass(frozen=True)
class MetricDelta:
    old: Any
    new: Any
    delta: Any = None

@dataclass(frozen=True)
class SummaryDiff:
    history_depth: MetricDelta
    facts_count: MetricDelta
    sessions: MetricDelta
    confidence: MetricDelta
    last_seen: MetricDelta

@dataclass(frozen=True)
class EngineDiff:
    added: Tuple[str, ...] = field(default_factory=tuple)
    removed: Tuple[str, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class CapabilityDiff:
    became_available: Tuple[str, ...] = field(default_factory=tuple)
    became_unavailable: Tuple[str, ...] = field(default_factory=tuple)
    state_changed: Tuple[str, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class Change:
    """
    Универсальная запись об изменении.
    Полностью иммутабельна.
    """
    change_id: str
    type: ChangeType
    subject: str          # e.g., "fact", "capability", "summary.facts"
    engine: str           # e.g., "usage", "presence", "system"
    category: str         # e.g., "behaviour", "network"
    old: Any
    new: Any
    delta: Any
    metadata: MappingProxyType  # Для FactChange: {"fact_id": "...", "changed_fields": [...]}

@dataclass(frozen=True)
class ProfileDiff:
    """
    Полностью автономный, иммутабельный объект различий.
    Не хранит ссылки на исходные UnifiedDeviceProfile.
    """
    identity_uuid: str
    diff_id: str                  # Детерминированный хэш
    created_at: datetime
    summary: SummaryDiff
    engine_diff: EngineDiff
    capability_diff: CapabilityDiff
    changes: Tuple[Change, ...]   # Tuple для гарантии иммутабельности

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def count(self) -> int:
        return len(self.changes)

    def __len__(self) -> int:
        return len(self.changes)

    def __iter__(self):
        return iter(self.changes)

    def to_dict(self) -> Dict[str, Any]:
        def custom_encoder(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, MappingProxyType):
                return dict(obj)
            return obj
        
        # Рекурсивное преобразование dataclass в dict
        def to_dict_recursive(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: to_dict_recursive(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, MappingProxyType):  # ИСПРАВЛЕНО: обработка MappingProxyType
                return {k: to_dict_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [to_dict_recursive(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: to_dict_recursive(v) for k, v in obj.items()}
            return custom_encoder(obj)
            
        return to_dict_recursive(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

# Глобальный пустой Diff для идемпотентности
EMPTY_DIFF = ProfileDiff(
    identity_uuid="",
    diff_id="empty",
    created_at=datetime.min,
    summary=SummaryDiff(
        history_depth=MetricDelta(None, None),
        facts_count=MetricDelta(0, 0),
        sessions=MetricDelta(0, 0),
        confidence=MetricDelta(0.0, 0.0),
        last_seen=MetricDelta(None, None)
    ),
    engine_diff=EngineDiff(),
    capability_diff=CapabilityDiff(),
    changes=tuple()
)
