#!/usr/bin/env python3
"""Query API — декларативный fluent API для UnifiedDeviceProfile."""
from typing import List, Optional, Any
from ...knowledge.service import KnowledgeService

class ProfileQueryBuilder:
    """
    Fluent Query Builder для Profile.
    
    Пример использования:
        profile.query().category("usage").confidence(60).all()
        profile.query().engine("presence").first()
        profile.query().tag("night").count()
    """
    
    def __init__(self, device_id: str, knowledge_service: KnowledgeService):
        self._device_id = device_id
        self._service = knowledge_service
        self._category: Optional[str] = None
        self._engine: Optional[str] = None
        self._tag: Optional[str] = None
        self._min_confidence: Optional[float] = None
        self._max_confidence: Optional[float] = None
        self._capability: Optional[str] = None
        self._fact_id: Optional[str] = None
    
    def category(self, category: str) -> 'ProfileQueryBuilder':
        """Фильтр по категории."""
        self._category = category
        return self
    
    def engine(self, engine: str) -> 'ProfileQueryBuilder':
        """Фильтр по движку."""
        self._engine = engine
        return self
    
    def tag(self, tag: str) -> 'ProfileQueryBuilder':
        """Фильтр по тегу."""
        self._tag = tag
        return self
    
    def confidence(self, min_confidence: float, max_confidence: float = 100.0) -> 'ProfileQueryBuilder':
        """Фильтр по диапазону уверенности."""
        self._min_confidence = min_confidence
        self._max_confidence = max_confidence
        return self
    
    def capability(self, capability_id: str) -> 'ProfileQueryBuilder':
        """Фильтр по возможности (соответствует категории)."""
        self._capability = capability_id
        return self
    
    def fact(self, fact_id: str) -> 'ProfileQueryBuilder':
        """Фильтр по ID факта."""
        self._fact_id = fact_id
        return self
    
    def _execute(self) -> List[Any]:
        """Выполняет запрос через KnowledgeService."""
        # Fact ID — специальный случай
        if self._fact_id:
            facts = self._service.get_all_facts(self._device_id)
            return [f for f in facts if f.id == self._fact_id]
        
        # Определяем стартовый фильтр
        if self._category or self._capability:
            cat = self._category or self._capability
            results = self._service.query_by_category(self._device_id, cat)
        elif self._engine:
            results = self._service.query_by_engine(self._device_id, self._engine)
        elif self._tag:
            results = self._service.query_by_tag(self._device_id, self._tag)
        else:
            results = self._service.get_all_facts(self._device_id)
        
        # Дополнительные фильтры
        if self._min_confidence is not None:
            results = [f for f in results if f.confidence >= self._min_confidence]
        
        if self._max_confidence is not None:
            results = [f for f in results if f.confidence <= self._max_confidence]
        
        return results
    
    def all(self) -> List[Any]:
        """Возвращает все результаты."""
        return self._execute()
    
    def first(self) -> Optional[Any]:
        """Возвращает первый результат."""
        results = self._execute()
        return results[0] if results else None
    
    def one(self) -> Optional[Any]:
        """Возвращает единственный результат (или None)."""
        results = self._execute()
        return results[0] if len(results) == 1 else None
    
    def exists(self) -> bool:
        """Проверяет существование результатов."""
        return len(self._execute()) > 0
    
    def count(self) -> int:
        """Подсчитывает количество результатов."""
        return len(self._execute())


class ProfileQueryAPI:
    """Точка входа для Query API."""
    
    def __init__(self, device_id: str, knowledge_service: KnowledgeService):
        self._device_id = device_id
        self._service = knowledge_service
    
    def __call__(self) -> ProfileQueryBuilder:
        """Возвращает новый QueryBuilder."""
        return ProfileQueryBuilder(self._device_id, self._service)
