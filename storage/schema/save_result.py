from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SaveResult:
    """
    Результат сохранения SnapshotBundle.
    Сообщает, что именно произошло в БД.
    """
    device_id: str = ""  # Реальный ID устройства в БД (критично для Event Engine)
    devices_created: int = 0
    devices_updated: int = 0
    snapshots_saved: int = 0
    observations_saved: int = 0
    evidence_saved: int = 0
    capabilities_saved: int = 0
    sessions_updated: int = 0
    elapsed_ms: float = 0.0
    success: bool = True
    error_message: str = ""
