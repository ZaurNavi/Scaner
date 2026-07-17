#!/usr/bin/env python3
"""ExplainService — независимый сервис для построения ExplainGraph."""
from typing import Dict, List, Any
from .graph import ExplainGraph
from ..profile import UnifiedDeviceProfile
from ...knowledge.service import KnowledgeService

class ExplainService:
    """
    Объясняет происхождение знаний в Profile.
    
    Независимый сервис — не метод Profile.
    """
    
    def __init__(self, knowledge_service: KnowledgeService):
        self._service = knowledge_service
    
    def build(self, profile: UnifiedDeviceProfile) -> ExplainGraph:
        """
        Строит ExplainGraph для Profile.
        
        Args:
            profile: UnifiedDeviceProfile
        
        Returns:
            ExplainGraph
        """
        snapshot = self._service.get_snapshot(profile.device_id)
        if not snapshot:
            return ExplainGraph(
                device_id=profile.device_id,
                facts_count=0,
                categories=[],
                engines=[],
                confidence_trace={}
            )
        
        categories = list(set(f.category for f in snapshot.facts)) if snapshot.facts else []
        engines = list(set(f.engine for f in snapshot.facts)) if snapshot.facts else []
        
        avg_confidence = sum(f.confidence for f in snapshot.facts) / len(snapshot.facts) if snapshot.facts else 0.0
        
        return ExplainGraph(
            device_id=profile.device_id,
            facts_count=len(snapshot.facts),
            categories=categories,
            engines=engines,
            confidence_trace={
                "overall": avg_confidence / 100.0,
                "knowledge": snapshot.coverage.fact_coverage / 100.0
            }
        )
