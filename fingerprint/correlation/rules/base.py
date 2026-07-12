#!/usr/bin/env python3
"""
Базовый класс для правил корреляции.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

from ..evidence import Evidence


@dataclass
class Rule:
    """
    Правило корреляции.
    
    when: функция (Evidence) -> bool
    then: словарь с результатами {os, model, device_type, vendor, confidence, reason}
    priority: чем выше, тем важнее правило
    """
    name: str
    when: Callable[[Evidence], bool]
    then: dict
    priority: int = 50
    
    def matches(self, evidence: Evidence) -> bool:
        """Проверяет, подходит ли правило под evidence."""
        try:
            return self.when(evidence)
        except Exception:
            return False
