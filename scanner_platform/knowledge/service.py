#!/usr/bin/env python3
"""Knowledge Service — фасад к Platform Facts."""
from typing import List, Dict, Any
from .snapshot import KnowledgeSnapshot
from .query import KnowledgeQuery
from .cache import KnowledgeCache
from .builders.summary import SummaryBuilder
from .builders.statistics import StatisticsBuilder
from .builders.coverage import CoverageBuilder
from ..cache.platform import VersionSnapshot

class KnowledgeService:
    """
    Knowledge Service — фасад к Platform Facts.
    
    ИСПРАВЛЕНО: не хранит Snapshot'ы, использует отдельный KnowledgeCache.
    """
    
    def __init__(self, cache: KnowledgeCache = None):
        self._cache = cache or KnowledgeCache()
    
    def create_snapshot(
        self,
        device_id: str,
        facts: List[Any],
        engine_results: Dict[str, Any] = None,
        version_snapshot: VersionSnapshot = None,
        history_service=None
    ) -> KnowledgeSnapshot:
        """
        Создает Knowledge Snapshot из Platform Facts.
        
        Args:
            device_id: Идентификатор устройства
            facts: Список Platform Facts
            engine_results: Dict[engine_name, EngineResult] для Coverage
            version_snapshot: Версии компонентов
            history_service: Для получения реальной истории
        
        Returns:
            KnowledgeSnapshot (immutable)
        """
        if version_snapshot is None:
            version_snapshot = VersionSnapshot()
        
        # Строим Summary (с History)
        summary = SummaryBuilder.build(device_id, facts, history_service)
        
        # Строим Statistics
        statistics = StatisticsBuilder.build(facts)
        
        # Строим Coverage из EngineResult
        coverage = CoverageBuilder.build(engine_results or {})
        
        # Создаем immutable Snapshot
        snapshot = KnowledgeSnapshot.create(
            device_id=device_id,
            version_snapshot=version_snapshot,
            facts=facts,
            summary=summary,
            statistics=statistics,
            coverage=coverage
        )
        
        # Кэшируем через отдельный KnowledgeCache
        self._cache.put(device_id, snapshot)
        
        return snapshot
    
    def get_snapshot(self, device_id: str) -> KnowledgeSnapshot:
        """Получает Snapshot устройства из кэша."""
        return self._cache.get(device_id)
    
    def query(self, device_id: str, query: KnowledgeQuery) -> List[Any]:
        """Выполняет запрос к Snapshot."""
        snapshot = self._cache.get(device_id)
        if not snapshot:
            return []
        
        return query.execute(snapshot)
    
    def invalidate(self, device_id: str):

            def query_by_category(self, device_id: str, category: str) -> List[Any]:
                
        """Публичный метод для запроса фактов по категории."""
        from .query import KnowledgeQuery
        snapshot = self._cache.get(device_id)
        if not snapshot:
            return []
        query = KnowledgeQuery(category=category)
        return query.execute(snapshot)
    
    def query_by_engine(self, device_id: str, engine: str) -> List[Any]:
        
        """Публичный метод для запроса фактов по движку."""
        from .query import KnowledgeQuery
        snapshot = self._cache.get(device_id)
        if not snapshot:
            return []
        query = KnowledgeQuery(engine=engine)
        return query.execute(snapshot)
    
    def query_by_tag(self, device_id: str, tag: str) -> List[Any]:
        """Публичный метод для запроса фактов по тегу."""
        from .query import KnowledgeQuery
        snapshot = self._cache.get(device_id)
        if not snapshot:
            return []
        query = KnowledgeQuery(tags=[tag])
        return query.execute(snapshot)
    
    def query_by_confidence(self, device_id: str, min_confidence: float) -> List[Any]:
        """Публичный метод для запроса фактов по уверенности."""
        from .query import KnowledgeQuery
        snapshot = self._cache.get(device_id)
        if not snapshot:
            return []
        query = KnowledgeQuery(confidence_min=min_confidence)
        return query.execute(snapshot)
    
    def get_all_facts(self, device_id: str) -> List[Any]:
        """Получает все факты устройства."""
        snapshot = self._cache.get(device_id)
        return list(snapshot.facts) if snapshot else []
        """Инвалидирует кэш для устройства."""
        self._cache.invalidate(device_id)
