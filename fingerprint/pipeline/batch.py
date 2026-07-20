#!/usr/bin/env python3
"""
UnifiedObservationBatch — официальный контракт Fingerprint.
ES-1.8.2: Batch является единственной единицей передачи данных между подсистемами.

Архитектура:
- UnifiedObservation: immutable наблюдение
- UnifiedObservationBatch: immutable коллекция с Collection API и Query API
- UnifiedObservationBatchBuilder: builder с инвалидацией после build()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

from ..normalization.models import (
    ObservationCategory,
    ObservationMetadata,
    UnifiedObservation,
)
from .exceptions import BuilderAlreadyBuiltError


# ==============================================================================
# UnifiedObservationBatch — immutable коллекция
# ==============================================================================

@dataclass(frozen=True)
class UnifiedObservationBatch:
    """
    Официальный контракт Fingerprint.
    
    ES-1.8.2:
    - Полностью immutable (frozen=True)
    - Collection API: __iter__, __len__, __contains__, count, first, last
    - Query API: query, filter, map, group_by, by_category, by_attribute, by_protocol, by_collector
    - Никакие list/tuple/dict наружу не возвращаются
    
    Zero Knowledge Principle:
    - Не содержит Profile, Session, Knowledge, History
    - Только UnifiedObservation
    """
    observations: Tuple[UnifiedObservation, ...]
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Валидация после создания."""
        # observations уже tuple благодаря frozen=True
        pass
    
    # ======================================================================
    # Collection API (пункт 9)
    # ======================================================================
    
    def __iter__(self) -> Iterator[UnifiedObservation]:
        """Итерация по наблюдениям."""
        return iter(self.observations)
    
    def __len__(self) -> int:
        """Количество наблюдений."""
        return len(self.observations)
    
    def __contains__(self, observation: UnifiedObservation) -> bool:
        """Проверка наличия наблюдения."""
        return observation in self.observations
    
    def count(self) -> int:
        """Количество наблюдений (алиас для __len__)."""
        return len(self.observations)
    
    def first(self) -> Optional[UnifiedObservation]:
        """Первое наблюдение или None."""
        return self.observations[0] if self.observations else None
    
    def last(self) -> Optional[UnifiedObservation]:
        """Последнее наблюдение или None."""
        return self.observations[-1] if self.observations else None
    
    def is_empty(self) -> bool:
        """Проверка на пустоту."""
        return len(self.observations) == 0
    
    # ======================================================================
    # Query API (пункт 10)
    # ======================================================================
    
    def query(self) -> BatchQuery:
        """
        Возвращает BatchQuery для fluent API.
        
        Использование:
            batch.query().by_category(ObservationCategory.IDENTITY).filter(...)
        """
        return BatchQuery(self.observations)
    
    def filter(self, predicate: Callable[[UnifiedObservation], bool]) -> UnifiedObservationBatch:
        """
        Фильтрует наблюдения по предикату.
        
        Возвращает новый UnifiedObservationBatch (immutable).
        """
        filtered = tuple(obs for obs in self.observations if predicate(obs))
        return UnifiedObservationBatch(
            observations=filtered,
            created_at=self.created_at,
            metadata=self.metadata
        )
    
    def map(self, transform: Callable[[UnifiedObservation], Any]) -> Tuple[Any, ...]:
        """
        Применяет трансформацию к каждому наблюдению.
        
        Возвращает tuple результатов.
        """
        return tuple(transform(obs) for obs in self.observations)
    
    def group_by(self, key_func: Callable[[UnifiedObservation], Any]) -> Dict[Any, Tuple[UnifiedObservation, ...]]:
        """
        Группирует наблюдения по ключу.
        
        Возвращает dict {key: tuple[UnifiedObservation, ...]}.
        """
        groups: Dict[Any, List[UnifiedObservation]] = {}
        for obs in self.observations:
            key = key_func(obs)
            if key not in groups:
                groups[key] = []
            groups[key].append(obs)
        
        return {k: tuple(v) for k, v in groups.items()}
    
    def by_category(self, category: ObservationCategory) -> UnifiedObservationBatch:
        """
        Фильтрует по категории.
        
        Возвращает новый UnifiedObservationBatch.
        """
        return self.filter(lambda obs: obs.category == category)
    
    def by_attribute(self, attribute: str) -> UnifiedObservationBatch:
        """
        Фильтрует по атрибуту.
        
        Возвращает новый UnifiedObservationBatch.
        """
        return self.filter(lambda obs: obs.attribute == attribute)
    
    def by_protocol(self, protocol: str) -> UnifiedObservationBatch:
        """
        Фильтрует по протоколу.
        
        Возвращает новый UnifiedObservationBatch.
        """
        return self.filter(lambda obs: obs.protocol == protocol)
    
    def by_collector(self, collector_id: str) -> UnifiedObservationBatch:
        """
        Фильтрует по collector_id.
        
        Возвращает новый UnifiedObservationBatch.
        """
        return self.filter(lambda obs: obs.collector_id == collector_id)
    
    # ======================================================================
    # Statistics
    # ======================================================================
    
    def categories(self) -> Tuple[ObservationCategory, ...]:
        """Уникальные категории."""
        return tuple(set(obs.category for obs in self.observations))
    
    def protocols(self) -> Tuple[str, ...]:
        """Уникальные протоколы."""
        return tuple(set(obs.protocol for obs in self.observations))
    
    def collectors(self) -> Tuple[str, ...]:
        """Уникальные collector_id."""
        return tuple(set(obs.collector_id for obs in self.observations))
    
    def attributes(self) -> Tuple[str, ...]:
        """Уникальные атрибуты."""
        return tuple(set(obs.attribute for obs in self.observations))


# ==============================================================================
# BatchQuery — fluent API для запросов
# ==============================================================================

@dataclass
class BatchQuery:
    """
    Fluent API для запросов к UnifiedObservationBatch.
    
    ES-1.8.2:
    - Цепочка вызовов
    - Immutable (каждый метод возвращает новый BatchQuery)
    """
    observations: Tuple[UnifiedObservation, ...]
    
    def by_category(self, category: ObservationCategory) -> BatchQuery:
        """Фильтрует по категории."""
        return BatchQuery(tuple(obs for obs in self.observations if obs.category == category))
    
    def by_attribute(self, attribute: str) -> BatchQuery:
        """Фильтрует по атрибуту."""
        return BatchQuery(tuple(obs for obs in self.observations if obs.attribute == attribute))
    
    def by_protocol(self, protocol: str) -> BatchQuery:
        """Фильтрует по протоколу."""
        return BatchQuery(tuple(obs for obs in self.observations if obs.protocol == protocol))
    
    def by_collector(self, collector_id: str) -> BatchQuery:
        """Фильтрует по collector_id."""
        return BatchQuery(tuple(obs for obs in self.observations if obs.collector_id == collector_id))
    
    def filter(self, predicate: Callable[[UnifiedObservation], bool]) -> BatchQuery:
        """Фильтрует по предикату."""
        return BatchQuery(tuple(obs for obs in self.observations if predicate(obs)))
    
    def with_confidence(self, min_confidence: float) -> BatchQuery:
        """Фильтрует по минимальной confidence."""
        return BatchQuery(tuple(obs for obs in self.observations if obs.confidence >= min_confidence))
    
    def all(self) -> Tuple[UnifiedObservation, ...]:
        """Возвращает все наблюдения как tuple."""
        return self.observations
    
    def first(self) -> Optional[UnifiedObservation]:
        """Первое наблюдение или None."""
        return self.observations[0] if self.observations else None
    
    def last(self) -> Optional[UnifiedObservation]:
        """Последнее наблюдение или None."""
        return self.observations[-1] if self.observations else None
    
    def count(self) -> int:
        """Количество наблюдений."""
        return len(self.observations)
    
    def is_empty(self) -> bool:
        """Проверка на пустоту."""
        return len(self.observations) == 0


# ==============================================================================
# UnifiedObservationBatchBuilder — builder с инвалидацией
# ==============================================================================

class UnifiedObservationBatchBuilder:
    """
    Builder для создания UnifiedObservationBatch.
    
    ES-1.8.2 (пункт 7):
    - add(), extend(), build()
    - После build() Builder автоматически инвалидируется
    - Любой вызов add(), extend(), build() после build() выбрасывает BuilderAlreadyBuiltError
    """
    
    def __init__(self):
        self._observations: List[UnifiedObservation] = []
        self._built: bool = False
    
    def _check_not_built(self):
        """Проверяет, что Builder ещё не был собран."""
        if self._built:
            raise BuilderAlreadyBuiltError("UnifiedObservationBatchBuilder")
    
    def add(self, observation: UnifiedObservation) -> UnifiedObservationBatchBuilder:
        """
        Добавляет одно наблюдение.
        
        Returns:
            self для цепочки вызовов
        
        Raises:
            BuilderAlreadyBuiltError: Если Builder уже был собран
        """
        self._check_not_built()
        self._observations.append(observation)
        return self
    
    def extend(self, observations: List[UnifiedObservation]) -> UnifiedObservationBatchBuilder:
        """
        Добавляет несколько наблюдений.
        
        Returns:
            self для цепочки вызовов
        
        Raises:
            BuilderAlreadyBuiltError: Если Builder уже был собран
        """
        self._check_not_built()
        self._observations.extend(observations)
        return self
    
    def build(self, metadata: Optional[Dict[str, Any]] = None) -> UnifiedObservationBatch:
        """
        Собирает UnifiedObservationBatch.
        
        После вызова build() Builder автоматически инвалидируется.
        
        Args:
            metadata: Опциональные метаданные для batch
        
        Returns:
            UnifiedObservationBatch (immutable)
        
        Raises:
            BuilderAlreadyBuiltError: Если Builder уже был собран
        """
        self._check_not_built()
        
        # Создаём immutable batch
        batch = UnifiedObservationBatch(
            observations=tuple(self._observations),
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        # Инвалидируем Builder
        self._built = True
        self._observations = []  # Освобождаем память
        
        return batch
    
    def is_built(self) -> bool:
        """Проверяет, был ли Builder уже собран."""
        return self._built
    
    def observation_count(self) -> int:
        """Количество добавленных наблюдений."""
        return len(self._observations)
