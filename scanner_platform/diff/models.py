#!/usr/bin/env python3
"""Модели данных для ProfileDiff."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import uuid

from .enums import ChangeType, Severity, ChangeReason

@dataclass(frozen=True)
class SummaryMetric:
    old: Any
    new: Any
    delta: Any = None

@dataclass(frozen=True)
class SummaryDiff:
    history_depth: SummaryMetric
    facts: SummaryMetric
    sessions: SummaryMetric
    confidence: SummaryMetric
    last_seen: SummaryMetric

@dataclass(frozen=True)
class EngineDiff:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class CapabilityDiff:
    became_available: List[str] = field(default_factory=list)
    became_unavailable: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class FactChange:
    fact_uuid: str
    changed_fields: List[str]
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]

@dataclass(frozen=True)
class Change:
    change_id: str
    type: ChangeType
    severity: Severity
    reason: ChangeReason
    engine: str
    category: str
    timestamp: datetime
    payload: Any  # FactChange, dict, или примитив

@dataclass
class ProfileDiff:
    """
    Полностью автономный объект различий.
    Не содержит ссылок на исходные UnifiedDeviceProfile.
    """
    identity_uuid: str
    diff_id: str
    created_at: datetime
    summary: SummaryDiff
    engine_diff: EngineDiff
    capability_diff: CapabilityDiff
    changes: List[Change] = field(default_factory=list)

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
            if hasattr(obj, 'to_dict'):
                return obj.to_dict()
            return asdict(obj)
        
        return json.loads(json.dumps(asdict(self), default=custom_encoder))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
