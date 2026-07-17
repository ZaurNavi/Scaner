#!/usr/bin/env python3
"""Unified Cache Platform."""
from dataclasses import dataclass

@dataclass
class VersionSnapshot:
    """
    Единый снимок версий для всей платформы.
    
    ИСПРАВЛЕНО: добавлен knowledge_version.
    """
    timeline_version: str = "1.0.0"
    metric_registry_version: str = "1.0.0"
    feature_registry_version: str = "1.0.0"
    rule_registry_version: str = "1.0.0"
    engine_version: str = "1.0.0"
    knowledge_version: str = "1.0.0"  # ДОБАВЛЕНО
    
    def to_cache_key(self) -> tuple:
        """Формирует единый ключ кэша."""
        return (
            self.timeline_version,
            self.metric_registry_version,
            self.feature_registry_version,
            self.rule_registry_version,
            self.engine_version,
            self.knowledge_version
        )
