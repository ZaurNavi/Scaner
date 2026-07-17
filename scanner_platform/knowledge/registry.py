#!/usr/bin/env python3
"""Knowledge Registry — реестр категорий знаний."""
from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum

class KnowledgeCategory(Enum):
    BEHAVIOUR = "behaviour"
    PRESENCE = "presence"
    USAGE = "usage"
    MOBILITY = "mobility"
    IDENTITY = "identity"
    RISK = "risk"

@dataclass
class KnowledgeDescriptor:
    """Дескриптор категории знаний."""
    category: KnowledgeCategory
    description: str
    providers: List[str] = field(default_factory=list)  # ДОБАВЛЕНО: какие движки предоставляют
    engines: List[str] = field(default_factory=list)    # ДОБАВЛЕНО: какие движки обрабатывают
    version: str = "1.0.0"

class KnowledgeRegistry:
    """Централизованный реестр категорий знаний."""
    
    _categories: Dict[str, KnowledgeDescriptor] = {}
    
    @classmethod
    def register(cls, descriptor: KnowledgeDescriptor):
        """Регистрирует категорию знаний."""
        cls._categories[descriptor.category.value] = descriptor
    
    @classmethod
    def get(cls, category: str) -> KnowledgeDescriptor:
        """Получает дескриптор категории."""
        return cls._categories.get(category)
    
    @classmethod
    def get_all(cls) -> Dict[str, KnowledgeDescriptor]:
        """Получает все категории."""
        return cls._categories.copy()
    
    @classmethod
    def get_by_engine(cls, engine: str) -> Dict[str, KnowledgeDescriptor]:
        """Получает категории, которые обрабатывает движок."""
        return {k: v for k, v in cls._categories.items() if engine in v.engines}
