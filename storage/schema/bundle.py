from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple, Optional
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
    Гарантирует, что все связанные сущности одного сканирования 
    будут сохранены в одной транзакции.
    """
    scan_id: str
    snapshot: Snapshot
    
    # Опционально: если устройство новое, передаем его. 
    device: Optional[Device] = None
    
    # Кортежи вместо списков для сохранения frozen=True
    observations: Tuple[Observation, ...] = field(default_factory=tuple)
    evidence: Tuple[Evidence, ...] = field(default_factory=tuple)
    capabilities: Tuple[Capability, ...] = field(default_factory=tuple)
    
    collector_log: Optional[CollectorLog] = None
