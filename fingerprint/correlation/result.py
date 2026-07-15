#!/usr/bin/env python3
"""
CorrelationResult — результат работы Correlation Engine.
Включает ConfidenceBreakdown для объяснения решений.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ConfidenceBreakdown:
    """
    Декомпозиция confidence по источникам.
    Позволяет объяснить, почему устройство определено именно так.
    """
    vendor: int = 0
    ttl: int = 0
    tcp: int = 0
    http: int = 0
    mdns: int = 0
    dns: int = 0
    omada: int = 0
    correlation: int = 0
    hostname: int = 0
    history: int = 0
    
    def total(self) -> int:
        """Суммарный confidence."""
        return min(
            self.vendor + self.ttl + self.tcp + self.http +
            self.mdns + self.dns + self.correlation +
            self.hostname + self.history,
            100
        )
    
    def to_dict(self) -> dict:
        """Для экспорта в JSON."""
        return {
            "vendor": self.vendor,
            "ttl": self.ttl,
            "tcp": self.tcp,
            "http": self.http,
            "mdns": self.mdns,
            "dns": self.dns,
            "correlation": self.correlation,
            "hostname": self.hostname,
            "history": self.history,
            "total": self.total(),
        }


@dataclass
class MatchedRule:
    """
    Информация о сработавшем правиле.
    Хранится в debug JSON для объяснения решений.
    """
    name: str
    confidence: int
    reason: str
    priority: int
    
    def to_dict(self) -> dict:
        """Для экспорта в JSON."""
        return {
            "name": self.name,
            "confidence": self.confidence,
            "reason": self.reason,
            "priority": self.priority,
        }


@dataclass
class CorrelationResult:
    """
    Результат работы Correlation Engine.
    Не мутирует Device — analysis.py сам решает, что применить.
    """
    
    os: str = ""
    model: str = ""
    device_type: str = ""
    vendor: str = ""
    confidence: int = 0
    
    # Теперь это список MatchedRule, а не просто строк
    matched_rules: list[MatchedRule] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    
    # Детализация confidence
    breakdown: ConfidenceBreakdown = field(default_factory=ConfidenceBreakdown)
    
    # Fingerprint Score — суммарная оценка
    fingerprint_score: int = 0
    
    def to_dict(self) -> dict:
        """Для экспорта в JSON."""
        return {
            "os": self.os,
            "model": self.model,
            "device_type": self.device_type,
            "vendor": self.vendor,
            "confidence": self.confidence,
            "fingerprint_score": self.fingerprint_score,
            "matched_rules": [r.to_dict() for r in self.matched_rules],
            "reasons": self.reasons,
            "breakdown": self.breakdown.to_dict(),
        }
