#!/usr/bin/env python3
"""KnowledgeFacade — абстракция над KnowledgeSnapshot для Builder."""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from .service import KnowledgeService

@dataclass
class KnowledgeFacade:
    """
    Facade над KnowledgeService.
    
    Builder работает ТОЛЬКО через этот Facade.
    Не знает внутреннюю структуру Snapshot.
    """
    
    def __init__(self, knowledge_service: KnowledgeService):
        self._service = knowledge_service
    
    def get_summary(self, device_id: str) -> Dict[str, Any]:
        """Получает Summary устройства."""
        snapshot = self._service.get_snapshot(device_id)
        return dict(snapshot.summary) if snapshot else {}
    
    def get_statistics(self, device_id: str) -> Dict[str, Any]:
        """Получает Statistics устройства."""
        snapshot = self._service.get_snapshot(device_id)
        return dict(snapshot.statistics) if snapshot else {}
    
    def get_coverage(self, device_id: str) -> Dict[str, float]:
        """Получает Coverage устройства."""
        snapshot = self._service.get_snapshot(device_id)
        if not snapshot:
            return {}
        cov = snapshot.coverage
        return {
            "timeline": cov.timeline_coverage,
            "metric": cov.metric_coverage,
            "feature": cov.feature_coverage,
            "rule": cov.rule_coverage,
            "fact": cov.fact_coverage
        }
    
    def get_confidence(self, device_id: str) -> float:
        """Получает среднюю уверенность."""
        snapshot = self._service.get_snapshot(device_id)
        if not snapshot or not snapshot.facts:
            return 0.0
        return sum(f.confidence for f in snapshot.facts) / len(snapshot.facts)
    
    def get_categories(self, device_id: str) -> List[str]:
        """Получает список категорий."""
        snapshot = self._service.get_snapshot(device_id)
        if not snapshot or not snapshot.facts:
            return []
        return list(set(f.category for f in snapshot.facts))
    
    def get_engines(self, device_id: str) -> List[str]:
        """Получает список движков."""
        snapshot = self._service.get_snapshot(device_id)
        if not snapshot or not snapshot.facts:
            return []
        return list(set(f.engine for f in snapshot.facts))
    
    def get_facts_count(self, device_id: str) -> int:
        """Получает количество фактов."""
        snapshot = self._service.get_snapshot(device_id)
        return len(snapshot.facts) if snapshot else 0
    
    def get_facts_by_category(self, device_id: str) -> Dict[str, int]:
        """Получает количество фактов по категориям."""
        snapshot = self._service.get_snapshot(device_id)
        if not snapshot or not snapshot.facts:
            return {}
        result = {}
        for fact in snapshot.facts:
            result[fact.category] = result.get(fact.category, 0) + 1
        return result
    
    def get_facts_by_engine(self, device_id: str) -> Dict[str, int]:
        """Получает количество фактов по движкам."""
        snapshot = self._service.get_snapshot(device_id)
        if not snapshot or not snapshot.facts:
            return {}
        result = {}
        for fact in snapshot.facts:
            result[fact.engine] = result.get(fact.engine, 0) + 1
        return result
    
    def get_highest_confidence(self, device_id: str) -> float:
        """Получает максимальную уверенность."""
        snapshot = self._service.get_snapshot(device_id)
        if not snapshot or not snapshot.facts:
            return 0.0
        return max(f.confidence for f in snapshot.facts)
    
    def get_presence_facts(self, device_id: str) -> List[Any]:
        """Получает факты Presence."""
        return self._service.query_by_category(device_id, "presence")
    
    def get_usage_facts(self, device_id: str) -> List[Any]:
        """Получает факты Usage."""
        return self._service.query_by_category(device_id, "usage")
    
    def get_behaviour_facts(self, device_id: str) -> List[Any]:
        """Получает факты Behaviour."""
        return self._service.query_by_category(device_id, "behaviour")
    
    def get_mobility_facts(self, device_id: str) -> List[Any]:
        """Получает факты Mobility."""
        return self._service.query_by_category(device_id, "mobility")
