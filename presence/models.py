#!/usr/bin/env python3
"""Модели данных Presence Engine с BaseAnalyticalValue и BaseProfile (Замечание №1, №15)."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from .categories import PresenceCategory, PresenceStatus, EventType

# Базовый класс для всех аналитических значений (Замечание №9: добавлен version)
@dataclass
class BaseAnalyticalValue:
    """Базовая модель для Metric и Feature. Используется всей платформой."""
    id: str
    name: str
    value: Any
    unit: str = ""
    version: str = "1.0.0"  # Замечание №9
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

@dataclass
class PresenceQuality:
    """Специфичное качество данных для Presence (Замечание №5, №6: добавлен freshness)."""
    coverage: float = 0.0
    samples: int = 0
    history_depth: int = 0
    freshness: float = 0.0  # Замечание №6
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

# PresenceMetricSet как dataclass (Замечание №1)
@dataclass
class PresenceMetricSet:
    """Контейнер для метрик с метаданными."""
    metrics: Dict[str, PresenceMetric] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    coverage: float = 0.0
    quality: PresenceQuality = field(default_factory=PresenceQuality)
    
    def get(self, metric_id: str) -> Optional[PresenceMetric]:
        return self.metrics.get(metric_id)
    
    def __getitem__(self, key: str) -> PresenceMetric:
        return self.metrics[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self.metrics
    
    def values(self):
        return self.metrics.values()
    
    def items(self):
        return self.metrics.items()

@dataclass
class TimelineEvent:  # Замечание №7: универсальный Timeline
    """Событие в Timeline. Переиспользуется всеми движками."""
    timestamp: datetime
    event_type: EventType
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Timeline:  # Замечание №7: универсальный Timeline
    """Универсальная модель Timeline для всех движков."""
    events: List[TimelineEvent] = field(default_factory=list)
    
    def is_immutable(self) -> bool:
        return True
    
    def get_by_type(self, event_type: EventType) -> List[TimelineEvent]:
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

# BaseProfile для унификации (Замечание №15)
@dataclass
class BaseProfile:
    """Базовый класс для всех Profile движков."""
    identity_id: str
    generated_at: datetime = field(default_factory=datetime.now)
    engine_version: str = "1.0.0"
    rules_version: str = "1.0.0"
    feature_version: str = "1.0.0"
    provider_version: str = "1.0.0"
    history_version: int = 1
    session_version: int = 1
    metric_coverage: float = 0.0
    feature_coverage: float = 0.0
    rule_match_ratio: float = 0.0  # Замечание №5: переименовано
    timeline: Timeline = field(default_factory=Timeline)
    metrics: PresenceMetricSet = field(default_factory=PresenceMetricSet)
    features: PresenceFeatureSet = field(default_factory=dict)
    facts: List[Any] = field(default_factory=list)

@dataclass
class PresenceProfile(BaseProfile):  # Замечание №15: наследуется от BaseProfile
    """Профиль Presence. Добавляет специфичные поля."""
    presence_version: int = 1

@dataclass
class PresenceExplanation:
    timeline: Timeline
    metrics: PresenceMetricSet
    features: PresenceFeatureSet
    matched_rules: List[str]
    skipped_rules: List[str]
    facts: List[PresenceFact]
    profile: PresenceProfile
    missing_features: List[str]
    providers: List[str]
    sources: List[str]
    execution_order: List[str] = field(default_factory=list)  # Замечание №10

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
    cache_hit: bool = False  # Замечание №14
    cache_key: Tuple = field(default_factory=tuple)  # Замечание №14
    engine_version: str = ""  # Замечание №14
    feature_version: str = ""  # Замечание №14
    provider_version: str = ""  # Замечание №14
