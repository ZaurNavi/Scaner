#!/usr/bin/env python3
"""ProfileResult — результат построения Profile (profile + execution)."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from .profile import UnifiedDeviceProfile

@dataclass
class ProfileExecution:
    """Информация о выполнении построения Profile."""
    started_at: datetime
    finished_at: datetime
    duration_ms: float
    cache_hit: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

@dataclass
class ProfileResult:
    """Результат построения Profile."""
    profile: UnifiedDeviceProfile
    execution: ProfileExecution
