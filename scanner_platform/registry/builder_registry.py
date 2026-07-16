#!/usr/bin/env python3
"""Builder Registry."""
from dataclasses import dataclass
from typing import Dict, Type, List
from ..builders.base import Builder  # <-- ИСПРАВЛЕНО на относительный импорт

@dataclass
class BuilderDescriptor:
    """Дескриптор Builder'а."""
    id: str
    builder_class: Type[Builder]
    version: str
    dependencies: List[str]

class BuilderRegistry:
    """Централизованный реестр Builder'ов."""
    
    _builders: Dict[str, BuilderDescriptor] = {}
    
    @classmethod
    def register(cls, name: str, builder_class: Type[Builder], version: str = "1.0.0", 
                 dependencies: List[str] = None):
        """Регистрирует Builder."""
        cls._builders[name] = BuilderDescriptor(
            id=name,
            builder_class=builder_class,
            version=version,
            dependencies=dependencies or []
        )
    
    @classmethod
    def get(cls, name: str) -> BuilderDescriptor:
        """Получает дескриптор Builder'а."""
        return cls._builders.get(name)
    
    @classmethod
    def get_all(cls) -> Dict[str, BuilderDescriptor]:
        """Получает все Builder'ы."""
        return cls._builders.copy()
