#!/usr/bin/env python3
"""Модели данных Mobility Engine."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

from .categories import MobilityCategory, MobilityStatus

@dataclass
class DataQuality:
    coverage: float = 0.0
    samples: int = 0
    freshness: float = 0.0  # 0.0 - 1.0
    continuity: float = 0.0 # 0.0 - 1.0
    confidence: float = 0.0

@dataclass
class Availability:
    available: bool = False
    reason: str = ""

@dataclass
class MobilityFeature:
    id: str
    name: str
    value: Any
    unit: str = ""
    confidence: float = 0.0
    data_quality: DataQuality = field(default_factory=DataQuality)
    availability: Availability = field(default_factory=Availability)
    sources: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    dependencies: List[str] = field(default_factory=list)

# FeatureSet - это dict, как требовалось в ТЗ
MobilityFeatureSet = Dict[str, MobilityFeature]

@dataclass
class MovementSegment:
    from_ap: Optional[str]
    to_ap: Optional[str]
    stay_time: float  # seconds
    signal_before: Optional[float]
    signal_after: Optional[float]
    transition_reason: str

@dataclass
class MobilityTimeline:
    segments: List[MovementSegment] = field(default_factory=list)

@dataclass
class MobilityFact:
    category: MobilityCategory
    feature: str
    value: Any
    measured_value: Any
    score: int
    confidence: float
    status: MobilityStatus
    matched_rules: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    reason: str = ""

@dataclass
class MobilityProfile:
    identity_id: str
    generated_at: datetime = field(default_factory=datetime.now)
    engine_version: str = "1.0.0"
    rules_version: str = "1.0.0"
    identity_version: int = 1
    history_version: int = 1
    session_version: int = 1
    behaviour_version: int = 1
    feature_coverage: float = 0.0
    mobility_coverage: float = 0.0
    features: MobilityFeatureSet = field(default_factory=dict)
    facts: List[MobilityFact] = field(default_factory=list)
    timeline: MobilityTimeline = field(default_factory=MobilityTimeline)

@dataclass
class MobilityExplanation:
    metrics: Dict[str, Any]
    features: MobilityFeatureSet
    matched_rules: List[str]
    skipped_rules: List[str]
    facts: List[MobilityFact]
    profile: MobilityProfile
    missing_features: List[str]
    providers: List[str]
    sources: List[str]

@dataclass
class DebugInfo:
    computation_time_ms: float
    used_providers: List[str]
    skipped_rules: List[str]
    missing_features: List[str]
    cache_invalidated: bool
    cache_reason: str
