#!/usr/bin/env python3
"""UnifiedDeviceProfile — единое представление устройства (immutable, чистый DTO)."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from .models import (
    ProfileSummary, ProfileStatistics, ProfileCoverage,
    ProfileConfidence, IdentityReference, ProfileCategories
)
from ..cache.platform import VersionSnapshot

@dataclass(frozen=True)
class UnifiedDeviceProfile:
    """
    Единое представление устройства (immutable, чистый DTO).
    
    НЕ содержит:
    - Snapshot
    - Facts
    - Timeline
    
    Всё через Query API и ExplainService.
    """
    device_id: str
    identity: IdentityReference
    summary: ProfileSummary
    categories: ProfileCategories
    statistics: ProfileStatistics
    coverage: ProfileCoverage
    confidence: ProfileConfidence
    capabilities: Dict[str, bool]
    version_snapshot: VersionSnapshot
    generated_at: datetime = field(default_factory=datetime.now)
    
    def is_immutable(self) -> bool:
        """Profile действительно immutable."""
        return True
