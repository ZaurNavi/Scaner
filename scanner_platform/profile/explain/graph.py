#!/usr/bin/env python3
"""Explain Graph — граф объяснений для UnifiedDeviceProfile."""
from dataclasses import dataclass, field
from typing import Dict, List, Any
from ...knowledge.snapshot import KnowledgeSnapshot

@dataclass(frozen=True)
class ExplainGraph:
    """
    Граф объяснений (immutable).
    
    Показывает происхождение всех знаний в Profile.
    """
    device_id: str
    facts_count: int
    categories: List[str]
    engines: List[str]
    confidence_trace: Dict[str, float] = field(default_factory=dict)
    
    @classmethod
    def build(cls, snapshot: KnowledgeSnapshot) -> 'ExplainGraph':
        """Строит ExplainGraph из Knowledge Snapshot."""
        categories = list(set(f.category for f in snapshot.facts)) if snapshot.facts else []
        engines = list(set(f.engine for f in snapshot.facts)) if snapshot.facts else []
        
        avg_confidence = sum(f.confidence for f in snapshot.facts) / len(snapshot.facts) if snapshot.facts else 0.0
        
        return cls(
            device_id=snapshot.device_id,
            facts_count=len(snapshot.facts),
            categories=categories,
            engines=engines,
            confidence_trace={
                "overall": avg_confidence / 100.0,
                "knowledge": snapshot.coverage.fact_coverage / 100.0
            }
        )
