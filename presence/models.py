#!/usr/bin/env python3
"""Модели данных Presence Engine с BaseAnalyticalValue (Замечание №4)."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from .categories import PresenceCategory, PresenceStatus, EventType

# Базовый класс для всех аналитических значений (Замечание №4)
@dataclass
class BaseAnalyticalValue:
    """Базовая модель для Metric и Feature. Используется всей платформой."""
    id: str
    name: str
    value: Any
    unit: str = ""
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

@dataclass
class PresenceQuality:
    """Специфичное качество данных для Presence (Замечание №5)."""
    coverage: float = 0.0
    samples: int = 0
    history_depth: int = 0  # дней
    confidence: float = 0.0
    reason: str = ""

@dataclass
class Availability:
    available: bool = False
    reason: str = ""

@dataclass
class PresenceMetric(BaseAnalyticalValue):
    """Метрика Presence. Наследуется от BaseAnalyticalValue."""
    quality: PresenceQuality = field(default_factory=PresenceQuality)
    availability: Availability = field(default_factory=Availability)

PresenceMetricSet = Dict[str, PresenceMetric]

@dataclass
class PresenceEvent:
    """Событие в Timeline (Замечание №6 — EventType enum)."""
    timestamp: datetime
    event_type: EventType
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PresenceTimeline:
    """
    Общая модель Timeline (Замечание №15).
    Переиспользуется Presence, Behaviour, Mobility, Role.
    """
    events: List[PresenceEvent] = field(default_factory=list)
    
    def is_immutable(self) -> bool:
        return True
    
    def get_by_type(self, event_type: EventType) -> List[PresenceEvent]:
        return [e for e in self.events if e.event_type == event_type]
    
    def count_by_type(self, event_type: EventType) -> int:
        return len(self.get_by_type(event_type))

@dataclass
class PresenceFeature(BaseAnalyticalValue):
    """Feature Presence. Наследуется от BaseAnalyticalValue."""
    coverage: float = 0.0
    samples: int = 0
    dependencies: List[str] = field(default_factory=list)
    availability: Availability = field(default_factory=Availability)

PresenceFeatureSet = Dict[str, PresenceFeature]

@dataclass
class PresenceFact:
    category: PresenceCategory
    feature: str
    value: Any
    measured_value: Any
    score: int
    confidence: float
    status: PresenceStatus
    matched_rules: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

@dataclass
class PresenceProfile:
    identity_id: str
    generated_at: datetime = field(default_factory=datetime.now)
    engine_version: str = "1.0.0"
    rules_version: str = "1.0.0"
    feature_version: str = "1.0.0"
    provider_version: str = "1.0.0"
    history_version: int = 1
    session_version: int = 1
    presence_version: int = 1
    metric_coverage: float = 0.0
    feature_coverage: float = 0.0
    fact_coverage: float = 0.0  # На самом деле Rule Match Ratio (Замечание №8)
    timeline: PresenceTimeline = field(default_factory=PresenceTimeline)
    metrics: PresenceMetricSet = field(default_factory=dict)  # Замечание №3: сохраняем
    features: PresenceFeatureSet = field(default_factory=dict)
    facts: List[PresenceFact] = field(default_factory=list)

@dataclass
class PresenceExplanation:
    timeline: PresenceTimeline
    metrics: PresenceMetricSet  # Замечание №14: реальные метрики
    features: PresenceFeatureSet
    matched_rules: List[str]
    skipped_rules: List[str]
    facts: List[PresenceFact]
    profile: PresenceProfile
    missing_features: List[str]
    providers: List[str]
    sources: List[str]

@dataclass
class DebugInfo:
    computation_time_ms: float
    provider_times: Dict[str, float] = field(default_factory=dict)
    builder_times: Dict[str, float] = field(default_factory=dict)
    feature_times: Dict[str, float] = field(default_factory=dict)
    evaluated_rules: List[str] = field(default_factory=list)
    matched_rules: List[str] = field(default_factory=list)
    skipped_rules: List[str] = field(default_factory=list)
    missing_features: List[str] = field(default_factory=list)
    cache_invalidated: bool = False
    cache_reason: str = ""
