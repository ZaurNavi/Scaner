#!/usr/bin/env python3
"""
Модели данных для Behaviour Engine (Унифицированная версия v1.6.1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

from .categories import BehaviourCategory, BehaviourStatus


@dataclass
class BehaviourFeature:
    """Объективный измеренный признак поведения."""
    name: str
    value: Any
    unit: str = ""
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class FeatureSet:
    """Набор всех вычисленных признаков для устройства."""
    average_session_duration: Optional[float] = None
    session_count: int = 0
    total_session_duration: float = 0.0
    peak_speed: Optional[float] = None
    average_speed: Optional[float] = None
    total_traffic: int = 0
    total_download: int = 0
    total_upload: int = 0
    idle_ratio: float = 0.0
    active_ratio: float = 0.0
    ap_changes: int = 0
    ssid_changes: int = 0
    rssi_variance: Optional[float] = None
    snr_variance: Optional[float] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    lifetime_seconds: Optional[float] = None
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result


@dataclass
class BehaviourFact:
    """Вывод о поведении на основе признаков."""
    category: BehaviourCategory
    feature: str
    value: Any  # ДОБАВЛЕНО: для совместимости с форматтером
    measured_value: Any
    threshold: Any
    score: int = 0  # ДОБАВЛЕНО: алиас для raw_score
    raw_score: int = 0
    confidence: float = 0.0
    status: BehaviourStatus = BehaviourStatus.UNKNOWN
    rule_id: str = ""
    matched_rules: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class BehaviourExplanation:
    """Объяснение поведенческого факта."""
    category: BehaviourCategory
    feature: str
    measured_value: Any
    threshold: Any
    raw_score: int
    confidence: float
    rule_id: str
    matched_rules: List[str]
    matched_features: List[str]
    sources: List[str]
    reasons: List[str]


@dataclass
class BehaviourSummary:
    """Краткая сводка поведенческих фактов."""
    facts_total: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    unknown: int = 0
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SourceVersions:
    """Версии источников данных."""
    identity_version: int = 1
    session_version: int = 1
    confidence_version: int = 1
    generated_from_timestamp: Optional[datetime] = None


# ДОБАВЛЕНО: DebugInfo для совместимости с форматтером
@dataclass
class DebugInfo:
    """Отладочная информация для Behaviour Engine."""
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
    cache_hit: bool = False
    cache_key: tuple = field(default_factory=tuple)
    engine_version: str = "1.0.0"
    feature_version: str = "1.0.0"
    provider_version: str = "1.0.0"


@dataclass
class BehaviourProfile:
    """Главный объект модуля Behaviour Engine (Унифицированный)."""
    identity_id: str
    generated_at: datetime = field(default_factory=datetime.now)
    engine_version: str = "1.0.0"
    rules_version: str = "1.0.0"
    feature_version: str = "1.0.0"  # ДОБАВЛЕНО
    provider_version: str = "1.0.0"  # ДОБАВЛЕНО
    metric_coverage: float = 0.0  # ДОБАВЛЕНО
    feature_coverage: float = 0.0
    rule_match_ratio: float = 0.0  # ДОБАВЛЕНО (алиас для behaviour_coverage)
    behaviour_coverage: float = 0.0
    features: FeatureSet = field(default_factory=FeatureSet)
    facts: List[BehaviourFact] = field(default_factory=list)
    summary: BehaviourSummary = field(default_factory=BehaviourSummary)
    source_versions: SourceVersions = field(default_factory=SourceVersions)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "generated_at": self.generated_at.isoformat(),
            "engine_version": self.engine_version,
            "rules_version": self.rules_version,
            "feature_version": self.feature_version,
            "provider_version": self.provider_version,
            "metric_coverage": self.metric_coverage,
            "feature_coverage": self.feature_coverage,
            "rule_match_ratio": self.rule_match_ratio,
            "behaviour_coverage": self.behaviour_coverage,
            "source_versions": {
                "identity_version": self.source_versions.identity_version,
                "session_version": self.source_versions.session_version,
                "confidence_version": self.source_versions.confidence_version
            },
            "summary": {
                "facts_total": self.summary.facts_total,
                "high": self.summary.high,
                "medium": self.summary.medium,
                "low": self.summary.low,
                "unknown": self.summary.unknown
            }
        }
