#!/usr/bin/env python3
"""Модели данных Usage Engine (все confidence в 0..100)."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

from .categories import UsageCategory, UsageStatus, EventType

@dataclass
class ProviderQuality:
    """Оценка качества данных от Provider (всё в 0..1)."""
    provider: str
    coverage: float = 0.0  # 0..1
    freshness: float = 0.0  # 0..1
    availability: float = 0.0  # 0..1 (было bool)
    latency_ms: float = 0.0
    errors: int = 0
    generated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"

@dataclass
class UsageQuality:
    """Общая оценка качества Usage (расширенная)."""
    coverage: float = 0.0
    freshness: float = 0.0
    samples: int = 0
    timeline_depth: int = 0
    confidence: float = 0.0
    metric_quality: Dict[str, float] = field(default_factory=dict)
    provider_quality: Dict[str, float] = field(default_factory=dict)  # ДОБАВЛЕНО
    timeline_quality: float = 0.0  # ДОБАВЛЕНО
    feature_quality: float = 0.0  # ДОБАВЛЕНО
    rule_quality: float = 0.0  # ДОБАВЛЕНО

@dataclass
class VersionSnapshot:
    """Снимок версий."""
    identity_version: str = "1.0.0"
    history_version: str = "1.0.0"
    traffic_version: str = "1.0.0"
    rules_version: str = "1.0.0"
    feature_version: str = "1.0.0"
    provider_version: str = "1.0.0"
    
    def to_cache_key(self) -> tuple:
        return (
            self.identity_version,
            self.history_version,
            self.traffic_version,
            self.rules_version,
            self.feature_version,
            self.provider_version
        )

@dataclass
class TrafficEvent:
    """Сырое событие трафика от Provider."""
    timestamp: datetime
    download_bytes: int
    upload_bytes: int
    flow_count: int = 0
    session_id: Optional[str] = None
    source: str = "traffic_provider"

@dataclass
class TimelineEvent:
    """Универсальное событие Timeline."""
    timestamp: datetime
    event_type: EventType
    payload: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 90.0  # 0..100
    sources: List[str] = field(default_factory=list)
    version: str = "1.0.0"

@dataclass
class Timeline:
    """Универсальный Timeline (read-only)."""
    events: List[TimelineEvent] = field(default_factory=list)
    
    def is_immutable(self) -> bool:
        return True
    
    def get_by_type(self, event_type: EventType) -> List[TimelineEvent]:
        return [e for e in self.events if e.event_type == event_type]
    
    def count_by_type(self, event_type: EventType) -> int:
        return len(self.get_by_type(event_type))

@dataclass
class UsageMetric:
    """Метрика Usage."""
    id: str
    name: str
    value: Any
    unit: str = ""
    analysis_window: str = "all_time"
    metric_version: str = "1.0.0"
    confidence: float = 90.0  # 0..100
    quality: ProviderQuality = None
    sources: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

@dataclass
class UsageMetricSet:
    """Контейнер для метрик."""
    metrics: Dict[str, UsageMetric] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    coverage: float = 0.0
    provider_quality: Dict[str, ProviderQuality] = field(default_factory=dict)
    
    def get(self, metric_id: str) -> Optional[UsageMetric]:
        return self.metrics.get(metric_id)
    
    def __getitem__(self, key: str) -> UsageMetric:
        return self.metrics[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self.metrics
    
    def values(self):
        return self.metrics.values()
    
    def items(self):
        return self.metrics.items()

@dataclass
class UsageFeature:
    """Feature Usage (ВСЕГДА существует, даже если False)."""
    id: str
    name: str
    value: Any
    unit: str = ""
    version: str = "1.0.0"
    confidence: float = 85.0  # 0..100
    quality: ProviderQuality = None
    sources: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    dependencies: List[str] = field(default_factory=list)
    availability: bool = True  # Feature всегда доступна
    availability_reason: str = ""
    interpretation: str = ""

UsageFeatureSet = Dict[str, UsageFeature]

@dataclass
class UsageFact:
    """Факт Usage с полным Explain Trace."""
    category: UsageCategory
    feature: str
    value: Any
    measured_value: Any
    score: int
    confidence: float  # 0..100
    quality: UsageQuality = None
    status: UsageStatus = UsageStatus.UNKNOWN
    matched_rules: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    explain_trace: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"

@dataclass
class UsageProfile:
    """Профиль Usage."""
    identity_id: str
    generated_at: datetime = field(default_factory=datetime.now)
    engine_version: str = "1.0.0"
    rules_version: str = "1.0.0"
    feature_version: str = "1.0.0"
    provider_version: str = "1.0.0"
    metrics_version: str = "1.0.0"
    timeline_version: str = "1.0.0"
    identity_version: int = 1
    history_version: int = 1
    session_version: int = 1
    metric_coverage: float = 0.0
    feature_coverage: float = 0.0
    rule_match_ratio: float = 0.0
    timeline: Timeline = field(default_factory=Timeline)
    metrics: UsageMetricSet = field(default_factory=UsageMetricSet)
    features: UsageFeatureSet = field(default_factory=dict)
    facts: List[UsageFact] = field(default_factory=list)
    quality: UsageQuality = field(default_factory=UsageQuality)
    version_snapshot: VersionSnapshot = field(default_factory=VersionSnapshot)

@dataclass
class UsageExplanation:
    """Полный Explain Trace."""
    timeline: Timeline
    metrics: UsageMetricSet
    provider_quality: Dict[str, ProviderQuality]
    features: UsageFeatureSet
    matched_rules: List[str]
    skipped_rules: List[str]
    facts: List[UsageFact]
    profile: UsageProfile
    missing_features: List[str]
    providers: List[str]
    sources: List[str]
    execution_order: List[str] = field(default_factory=list)
    confidence_trace: Dict[str, float] = field(default_factory=dict)

@dataclass
class DebugInfo:
    """Отладочная информация."""
    computation_time_ms: float
    provider_times: Dict[str, float] = field(default_factory=dict)
    builder_times: Dict[str, float] = field(default_factory=dict)
    feature_times: Dict[str, float] = field(default_factory=dict)
    evaluated_rules: List[str] = field(default_factory=list)
    matched_rules: List[str] = field(default_factory=list)
    skipped_rules: List[str] = field(default_factory=list)
    missing_features: List[str] = field(default_factory=list)
    all_rules: List[Any] = field(default_factory=list)  # ДОБАВЛЕНО
    cache_invalidated: bool = False
    cache_reason: str = ""
    cache_hit: bool = False
    cache_key: tuple = field(default_factory=tuple)
    engine_version: str = "1.0.0"
    feature_version: str = "1.0.0"
    provider_version: str = "1.0.0"
