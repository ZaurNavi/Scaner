#!/usr/bin/env python3
"""
Модели данных для Confidence Service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

from .categories import FactCategory


class FactStatus(Enum):
    """Статус вычислимости факта."""
    UNKNOWN = "UNKNOWN"
    EVALUATED = "EVALUATED"
    CONFLICT = "CONFLICT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class FactAssessment:
    """Оценка одного факта."""
    category: FactCategory
    value: str
    raw_score: int = 0
    confidence: float = 0.0
    status: FactStatus = FactStatus.UNKNOWN
    sources: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ConfidenceSummary:
    """Краткая сводка лучших оценок."""
    vendor: Optional[FactAssessment] = None
    model: Optional[FactAssessment] = None
    hostname: Optional[FactAssessment] = None
    os: Optional[FactAssessment] = None
    device_type: Optional[FactAssessment] = None


@dataclass
class ConfidenceStatistics:
    """Статистика оценок."""
    total_facts: int = 0
    evaluated: int = 0
    conflicts: int = 0
    insufficient_data: int = 0
    unknown: int = 0


@dataclass
class ConfidenceProfile:
    """Главный результат работы Confidence Service."""
    identity_id: str
    generated_at: datetime = field(default_factory=datetime.now)
    facts: Dict[FactCategory, List[FactAssessment]] = field(default_factory=dict)
    summary: ConfidenceSummary = field(default_factory=ConfidenceSummary)
    coverage: float = 0.0
    statistics: ConfidenceStatistics = field(default_factory=ConfidenceStatistics)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация для вывода."""
        return {
            "identity_id": self.identity_id,
            "generated_at": self.generated_at.isoformat(),
            "coverage": self.coverage,
            "statistics": {
                "total_facts": self.statistics.total_facts,
                "evaluated": self.statistics.evaluated,
                "conflicts": self.statistics.conflicts,
                "insufficient_data": self.statistics.insufficient_data,
                "unknown": self.statistics.unknown
            },
            "summary": {
                "vendor": self.summary.vendor.confidence if self.summary.vendor else None,
                "model": self.summary.model.confidence if self.summary.model else None,
                "hostname": self.summary.hostname.confidence if self.summary.hostname else None,
                "os": self.summary.os.confidence if self.summary.os else None,
                "device_type": self.summary.device_type.confidence if self.summary.device_type else None
            }
        }
