#!/usr/bin/env python3
"""Модели Behaviour Engine — профили, признаки, факты."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class SourceVersions:
    """Версии источников данных."""
    timeline_version: str = "1.0.0"
    metric_version: str = "1.0.0"
    feature_version: str = "1.0.0"
    rule_version: str = "1.0.0"

@dataclass
class DebugInfo:
    """Отладочная информация."""
    computation_time_ms: float = 0.0
    cache_hit: bool = False
    cache_key: tuple = ()
    provider_times: Dict[str, float] = field(default_factory=dict)
    builder_times: Dict[str, float] = field(default_factory=dict)
    feature_times: Dict[str, float] = field(default_factory=dict)
    skipped_rules: List[str] = field(default_factory=list)
    missing_features: List[str] = field(default_factory=list)

@dataclass
class FeatureSet:
    """Набор вычисленных признаков."""
    generated_at: datetime = field(default_factory=datetime.now)
    average_session_duration: Optional[float] = None
    session_count: int = 0
    total_session_duration: float = 0.0
    peak_speed: Optional[float] = None
    average_speed: Optional[float] = None
    total_traffic: int = 0
    idle_ratio: float = 0.0
    active_ratio: float = 0.0
    ap_changes: int = 0
    ssid_changes: int = 0
    lifetime_seconds: Optional[float] = None

@dataclass
class BehaviourSummary:
    """Краткая сводка поведения."""
    facts_total: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    unknown: int = 0

@dataclass
class BehaviourProfile:
    """Профиль поведения устройства."""
    identity_id: str
    generated_at: datetime
    engine_version: str
    rules_version: str
    feature_version: str
    provider_version: str
    metric_coverage: float
    feature_coverage: float
    rule_match_ratio: float
    behaviour_coverage: float
    features: Optional[FeatureSet]
    facts: List[Any]
    summary: BehaviourSummary
    source_versions: SourceVersions
