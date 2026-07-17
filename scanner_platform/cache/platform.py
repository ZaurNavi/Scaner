#!/usr/bin/env python3
"""Unified Cache Platform."""
from dataclasses import dataclass

@dataclass
class VersionSnapshot:
    """
    Единый снимок версий для всей платформы.
    
    Расширен для v1.6.6: добавлены profile_version и profile_schema_version.
    """
    timeline_version: str = "1.0.0"
    metric_version: str = "1.0.0"
    feature_version: str = "1.0.0"
    rule_version: str = "1.0.0"
    knowledge_version: str = "1.0.0"
    profile_version: str = "1.0.0"  # ДОБАВЛЕНО
    profile_schema_version: str = "1.0.0"  # ДОБАВЛЕНО
    
    def to_cache_key(self) -> tuple:
        """Формирует единый ключ кэша."""
        return (
            self.timeline_version,
            self.metric_version,
            self.feature_version,
            self.rule_version,
            self.knowledge_version,
            self.profile_version,
            self.profile_schema_version
        )
