#!/usr/bin/env python3
"""Knowledge Snapshot — immutable единый объект знаний платформы."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Tuple
from types import MappingProxyType
from ..cache.platform import VersionSnapshot
from ..coverage.platform import Coverage
from .indexes.fact_index import FactIndex

@dataclass
class KnowledgeSnapshot:
    """
    Единый объект знаний платформы.
    
    ДЕЙСТВИТЕЛЬНО immutable:
    - facts: tuple (неизменяемый)
    - summary: MappingProxyType (неизменяемый dict)
    - statistics: MappingProxyType (неизменяемый dict)
    """
    device_id: str
    version_snapshot: VersionSnapshot
    facts: Tuple[Any, ...]  # ИСПРАВЛЕНО: tuple вместо list
    summary: MappingProxyType  # ИСПРАВЛЕНО: immutable dict
    statistics: MappingProxyType  # ИСПРАВЛЕНО: immutable dict
    coverage: Coverage
    generated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Строит ленивые индексы после создания."""
        self._indexes = FactIndex(list(self.facts))
    
    @property
    def indexes(self) -> FactIndex:
        """Возвращает индексы."""
        return self._indexes
    
    def is_immutable(self) -> bool:
        """Snapshot действительно immutable."""
        return True
    
    @classmethod
    def create(
        cls,
        device_id: str,
        version_snapshot: VersionSnapshot,
        facts: List[Any],
        summary: Dict[str, Any],
        statistics: Dict[str, Any],
        coverage: Coverage
    ) -> 'KnowledgeSnapshot':
        """
        Фабричный метод для создания immutable Snapshot.
        
        Преобразует list в tuple, dict в MappingProxyType.
        """
        return cls(
            device_id=device_id,
            version_snapshot=version_snapshot,
            facts=tuple(facts),  # ИСПРАВЛЕНО: tuple для immutability
            summary=MappingProxyType(summary),  # ИСПРАВЛЕНО: immutable dict
            statistics=MappingProxyType(statistics),  # ИСПРАВЛЕНО: immutable dict
            coverage=coverage
        )
