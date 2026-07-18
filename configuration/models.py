#!/usr/bin/env python3
"""Модели данных Configuration Layer."""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Type

@dataclass(frozen=True)
class ConfigValue:
    """Публичный контракт параметра конфигурации."""
    id: str
    name: str
    group: str
    type: Type
    default: Any
    description: str
    validator: Optional[Callable[[Any], bool]] = None
    mutable: bool = False
    deprecated: bool = False

@dataclass(frozen=True)
class ConfigGroup:
    """Логическая группа параметров."""
    name: str
    description: str
    parameters: list = field(default_factory=list)
