#!/usr/bin/env python3
"""
Модели данных для Behaviour Engine.
Разделение: FeatureSet (измерения) vs BehaviourFact (интерпретация).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

from .categories import BehaviourCategory, BehaviourStatus


@dataclass
class BehaviourFeature:
    """Объективный измеренный признак поведения (сырой факт)."""
    name: str
    value: Any
    unit: str = ""
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class FeatureSet:
    """Набор всех вычисленных признаков для устройства (измерения)."""
    # Сессии
    average_session_duration: Optional[float] = None  # секунды
    session_count: int = 0
    total_session_duration: float = 0.0  # секунды
    
    # Трафик
    peak_speed: Optional[float] = None  # Mbps
    average_speed: Optional[float] = None  # Mbps
    total_traffic: int = 0  # байты
    total_download: int = 0  # байты
    total_upload: int = 0  # байты
    
    # Активность
    idle_ratio: float = 0.0  # 0.0 - 1.0
    active_ratio: float = 0.0  # 0.0 - 1.0
    
    # Мобильность
    ap_changes: int = 0
    ssid_changes: int = 0
    
    # Сигнал
    rssi_variance: Optional[float] = None  # dB
    snr_variance: Optional[float] = None  # dB
    
    # Время
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    lifetime_seconds: Optional[float] = None  # секунды
    
    # Метаданные
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация для отладки."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result


@dataclass
class BehaviourFact:
    """Вывод о поведении на основе признаков (интерпретация)."""
    category: BehaviourCategory
    feature: str  # Имя признака, на основе которого сделан вывод
    measured_value: Any  # Измеренное значение
    threshold: Any  # Порог из правила
    raw_score: int = 0
    confidence: float = 0.0
    status: BehaviourStatus = BehaviourStatus.UNKNOWN
    rule_id: str = ""  # ID правила (RULE-0001)
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
    matched_features: List[str]  # Все признаки, участвовавшие в выводе
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
    """Версии источников данных для воспроизводимости."""
    identity_version: int = 1
    session_version: int = 1
    confidence_version: int = 1
    generated_from_timestamp: Optional[datetime] = None


@dataclass
class BehaviourProfile:
    """Главный объект модуля Behaviour Engine."""
    identity_id: str
    generated_at: datetime = field(default_factory=datetime.now)
    engine_version: str = "1.0.0"
    rules_version: str = "1.0.0"
    feature_coverage: float = 0.0
    behaviour_coverage: float = 0.0
    features: FeatureSet = field(default_factory=FeatureSet)
    facts: List[BehaviourFact] = field(default_factory=list)  # Изменено с Dict на List
    summary: BehaviourSummary = field(default_factory=BehaviourSummary)
    source_versions: SourceVersions = field(default_factory=SourceVersions)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация для вывода."""
        return {
            "identity_id": self.identity_id,
            "generated_at": self.generated_at.isoformat(),
            "engine_version": self.engine_version,
            "rules_version": self.rules_version,
            "feature_coverage": self.feature_coverage,
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
