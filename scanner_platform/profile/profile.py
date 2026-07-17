#!/usr/bin/env python3
"""UnifiedDeviceProfile — единое представление устройства (immutable)."""
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Dict, Any, Optional
from .models import ProfileSummary, ProfileStatistics, ProfileCoverage, ProfileConfidence
from .query.api import ProfileQueryAPI
from .explain.graph import ExplainGraph
from ..cache.platform import VersionSnapshot

@dataclass(frozen=True)
class UnifiedDeviceProfile:
    """
    Единое представление устройства (immutable).
    
    НЕ содержит открытого списка Facts.
    Доступ к фактам только через Query API.
    """
    device_id: str
    identity: Dict[str, Any]
    summary: ProfileSummary
    categories: Dict[str, Any]
    statistics: ProfileStatistics
    coverage: ProfileCoverage
    confidence: ProfileConfidence
    capabilities: Dict[str, bool]
    version_snapshot: VersionSnapshot
    generated_at: datetime = field(default_factory=datetime.now)
    _snapshot: Any = field(repr=False, compare=False)  # Скрытый Snapshot для Query API
    
    def query(self) -> ProfileQueryAPI:
        """Возвращает Query API."""
        return ProfileQueryAPI(self._snapshot)
    
    def explain(self) -> ExplainGraph:
        """Возвращает Explain Graph."""
        return ExplainGraph.build(self._snapshot)
    
    def is_immutable(self) -> bool:
        """Profile действительно immutable."""
        return True
