#!/usr/bin/env python3
"""Модели Behaviour Engine — EngineResult и EngineStatistics."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
from ..coverage.platform import Coverage
from ..cache.platform import VersionSnapshot

@dataclass
class EngineStatistics:
    """Статистика работы движка."""
    metrics_computed: int = 0
    features_computed: int = 0
    rules_evaluated: int = 0
    rules_matched: int = 0
    rules_skipped: int = 0
    facts_generated: int = 0
    computation_time_ms: float = 0.0

@dataclass
class EngineResult:
    """
    Единый результат работы любого движка платформы.
    Никаких BehaviourResult — только EngineResult.
    """
    device_id: str
    engine: str = "behaviour"
    facts: List[Any] = field(default_factory=list)
    coverage: Coverage = field(default_factory=Coverage)
    statistics: EngineStatistics = field(default_factory=EngineStatistics)
    debug: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    explain: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    version_snapshot: VersionSnapshot = field(default_factory=VersionSnapshot)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "engine": self.engine,
            "facts_count": len(self.facts),
            "coverage": self.coverage.to_dict(),
            "statistics": {
                "metrics_computed": self.statistics.metrics_computed,
                "features_computed": self.statistics.features_computed,
                "rules_evaluated": self.statistics.rules_evaluated,
                "rules_matched": self.statistics.rules_matched,
                "facts_generated": self.statistics.facts_generated,
                "computation_time_ms": self.statistics.computation_time_ms,
            },
            "version": self.version,
            "generated_at": self.generated_at.isoformat()
        }
