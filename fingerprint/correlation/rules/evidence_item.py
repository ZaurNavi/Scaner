#!/usr/bin/env python3
"""
EvidenceItem — один факт об устройстве с вкладом в confidence.
Используется для объяснения решений Correlation Engine.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class EvidenceItem:
    """
    Один факт об устройстве.
    
    Примеры:
    - "Vendor = Huawei" (+10)
    - "TTL = 64 → Linux" (+40)
    - "Rule: android_rule" (+25)
    """
    
    # Описание факта (например, "Vendor = Huawei")
    description: str
    
    # Вклад в confidence (например, 10)
    contribution: int
    
    # Источник факта (например, "vendor", "ttl", "rule:android_rule")
    source: str
    
    # Дополнительная информация (например, "TTL=64", "sysDescr=RouterOS")
    details: str = ""
    
    def to_dict(self) -> dict:
        """Для экспорта в JSON."""
        return {
            "description": self.description,
            "contribution": self.contribution,
            "source": self.source,
            "details": self.details,
        }
    
    def __str__(self) -> str:
        """Форматирование для консоли."""
        if self.details:
            return f"✔ {self.description} ({self.details}) [+{self.contribution}]"
        return f"✔ {self.description} [+{self.contribution}]"
