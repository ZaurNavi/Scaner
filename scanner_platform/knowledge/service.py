#!/usr/bin/env python3
"""Knowledge Service — фасад к Platform Facts.

v1.6.9.8: Интеграция с Configuration Layer.
Принимает ConfigurationManager через DI.
"""
from typing import List, Dict, Any, Optional
from .snapshot import KnowledgeSnapshot
from .query import KnowledgeQuery
from .cache import KnowledgeCache
from .builders.summary import SummaryBuilder
from .builders.statistics import StatisticsBuilder
from .builders.coverage import CoverageBuilder
from ..cache.platform import VersionSnapshot

# v1.6.9.8: Configuration Layer Integration
from configuration import ConfigurationManager


class KnowledgeService:
    """
    Knowledge Service — фасад к Platform Facts.

    v1.6.9.8: Принимает ConfigurationManager через конструктор (Dependency Injection).
    Не хранит Snapshot'ы напрямую, использует отдельный KnowledgeCache.
    """

    def __init__(
        self,
        cache: Optional[KnowledgeCache] = None,
        configuration: Optional[ConfigurationManager] = None
    ):
        """
        v1.6.9.8: Конструктор с Dependency Injection.
        
        Args:
            cache: KnowledgeCache (опционально, создаётся автоматически)
            configuration: ConfigurationManager (опционально)
        """
        # v1.6.9.8: Если cache не передан, создаём с configuration
        if cache is not None:
            self._cache = cache
        else:
            self._cache = KnowledgeCache(configuration=configuration)
        
        self.configuration = configuration

    def create_snapshot(
        self,
        device_id: str,
        facts: List[Any],
        engine_results: Dict[str, Any] = None,
        version_snapshot: VersionSnapshot = None,
        history_service=None
    ) -> KnowledgeSnapshot:
        """Создает Knowledge Snapshot из Platform Facts."""
        if version_snapshot is None:
            version_snapshot = VersionSnapshot()

        summary = SummaryBuilder.build(device_id, facts, history_service)
        statistics = StatisticsBuilder.build(facts)
        coverage = CoverageBuilder.build(engine_results or {})

        snapshot = KnowledgeSnapshot.create(
            device_id=device_id,
            version_snapshot=version_snapshot,
            facts=facts,
            summary=summary,
            statistics=statistics,
            coverage=coverage
        )

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
        """Инвалидирует кэш для устройства."""
        self._cache.invalidate(device_id)

    # === ПУБЛИЧНЫЕ МЕТОДЫ ДЛЯ QUERY (v1.6.6) ===

    def query_by_category(self, device_id: str, category: str) -> List[Any]:
        """Публичный метод для запроса фактов по категории."""
        snapshot = self._cache.get(device_id)
        if not snapshot:
            return []
        query = KnowledgeQuery(category=category)
        return query.execute(snapshot)

    def query_by_engine(self, device_id: str, engine: str) -> List[Any]:
        """Публичный метод для запроса фактов по движку."""
        snapshot = self._cache.get(device_id)
        if not snapshot:
            return []
        query = KnowledgeQuery(engine=engine)
        return query.execute(snapshot)

    def query_by_tag(self, device_id: str, tag: str) -> List[Any]:
        """Публичный метод для запроса фактов по тегу."""
        snapshot = self._cache.get(device_id)
        if not snapshot:
            return []
        query = KnowledgeQuery(tags=[tag])
        return query.execute(snapshot)

    def query_by_confidence(self, device_id: str, min_confidence: float) -> List[Any]:
        """Публичный метод для запроса фактов по уверенности."""
        snapshot = self._cache.get(device_id)
        if not snapshot:
            return []
        query = KnowledgeQuery(confidence_min=min_confidence)
        return query.execute(snapshot)

    def get_all_facts(self, device_id: str) -> List[Any]:
        """Получает все факты устройства."""
        snapshot = self._cache.get(device_id)
        return list(snapshot.facts) if snapshot else []
    
    def cache_info(self) -> Dict[str, Any]:
        """Возвращает информацию о кэше."""
        return {
            "size": self._cache.size(),
            "max_size": self._cache.max_size()
        }
