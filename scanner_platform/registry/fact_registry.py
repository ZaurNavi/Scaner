#!/usr/bin/env python3
"""Fact Registry — декларативное описание Platform Facts."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

class FactSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class FactDescriptor:
    """Дескриптор Platform Fact."""
    id: str
    engine: str
    category: str
    description: str
    severity: FactSeverity = FactSeverity.LOW
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"

class FactRegistry:
    """Централизованный реестр фактов."""
    
    _facts: Dict[str, FactDescriptor] = {}
    
    @classmethod
    def register(cls, descriptor: FactDescriptor):
        """Регистрирует факт."""
        cls._facts[descriptor.id] = descriptor
    
    @classmethod
    def get(cls, fact_id: str) -> Optional[FactDescriptor]:
        """Получает дескриптор факта по ID."""
        return cls._facts.get(fact_id)
    
    @classmethod
    def get_all(cls) -> Dict[str, FactDescriptor]:
        """Получает все факты."""
        return cls._facts.copy()
    
    @classmethod
    def get_by_category(cls, category: str) -> Dict[str, FactDescriptor]:
        """Получает факты по категории."""
        return {k: v for k, v in cls._facts.items() if v.category == category}
    
    @classmethod
    def get_by_engine(cls, engine: str) -> Dict[str, FactDescriptor]:
        """Получает факты по движку."""
        return {k: v for k, v in cls._facts.items() if v.engine == engine}
    
    @classmethod
    def get_by_tag(cls, tag: str) -> Dict[str, FactDescriptor]:
        """Получает факты по тегу."""
        return {k: v for k, v in cls._facts.items() if tag in v.tags}
