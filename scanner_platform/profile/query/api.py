#!/usr/bin/env python3
"""Query API — декларативный API для UnifiedDeviceProfile."""
from typing import List, Optional, Any
from ...knowledge.snapshot import KnowledgeSnapshot
from ...knowledge.query import KnowledgeQuery

class ProfileQueryAPI:
    """
    Декларативный Query API для UnifiedDeviceProfile.
    
    Все запросы используют индексы (не полный перебор).
    """
    
    def __init__(self, snapshot: KnowledgeSnapshot):
        self.snapshot = snapshot
    
    def by_category(self, category: str) -> List[Any]:
        """Запрос по категории."""
        query = KnowledgeQuery(category=category)
        return query.execute(self.snapshot)
    
    def by_fact(self, fact_id: str) -> Optional[Any]:
        """Запрос по ID факта."""
        return self.snapshot.indexes.get_by_id(fact_id)
    
    def by_engine(self, engine: str) -> List[Any]:
        """Запрос по движку."""
        query = KnowledgeQuery(engine=engine)
        return query.execute(self.snapshot)
    
    def by_capability(self, capability_id: str) -> List[Any]:
        """Запрос по возможности (упрощённо — по категории)."""
        # Capability обычно соответствует категории
        return self.by_category(capability_id)
    
    def by_tag(self, tag: str) -> List[Any]:
        """Запрос по тегу."""
        query = KnowledgeQuery(tags=[tag])
        return query.execute(self.snapshot)
    
    def by_confidence(self, min_confidence: float, max_confidence: float = 100.0) -> List[Any]:
        """Запрос по диапазону уверенности."""
        query = KnowledgeQuery(confidence_range=(min_confidence, max_confidence))
        return query.execute(self.snapshot)
    
    def first(self) -> Optional[Any]:
        """Получить первый факт."""
        results = self.all()
        return results[0] if results else None
    
    def one(self) -> Optional[Any]:
        """Получить единственный факт (или None, если их больше одного)."""
        results = self.all()
        return results[0] if len(results) == 1 else None
    
    def exists(self) -> bool:
        """Проверить существование фактов."""
        return len(self.snapshot.facts) > 0
    
    def count(self) -> int:
        """Подсчитать количество фактов."""
        return len(self.snapshot.facts)
    
    def all(self) -> List[Any]:
        """Получить все факты."""
        query = KnowledgeQuery()
        return query.execute(self.snapshot)
