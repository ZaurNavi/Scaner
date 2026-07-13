from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple, Optional
from .scan import Scan
from .device import Device
from .snapshot import Snapshot
from .observation import Observation
from .evidence import Evidence
from .capability import Capability
from .collector_log import CollectorLog

@dataclass(frozen=True)
class SnapshotBundle:
    """
    Атомарный пакет данных для сохранения за один проход.
    """
    snapshot: Snapshot
    scan_id: str  # Оставляем для обратной совместимости, но теперь есть и scan
    
    scan: Optional[Scan] = None
    device: Optional[Device] = None
    
    observations: Tuple[Observation, ...] = field(default_factory=tuple)
    evidence: Tuple[Evidence, ...] = field(default_factory=tuple)
    capabilities: Tuple[Capability, ...] = field(default_factory=tuple)
    collector_log: Optional[CollectorLog] = None
