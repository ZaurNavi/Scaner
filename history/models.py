#!/usr/bin/env python3
"""
Модели данных для History Service.
Только базовые записи, без знания о специфичных контроллерах.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SnapshotRecord:
    """Запись снимка состояния устройства."""
    id: str
    scan_id: str
    device_id: str
    timestamp: datetime
    ip: str
    hostname: str | None
    os: str | None
    model: str | None
    device_type: str | None
    confidence: int


@dataclass
class ObservationRecord:
    """Запись наблюдения из коллектора."""
    id: str
    snapshot_id: str
    source: str
    key: str
    value: str  # Теперь это JSON-строка
    obs_type: str
    unit: str | None
    confidence: int | None
    timestamp: datetime | None = None


@dataclass
class EventRecord:
    """Запись события."""
    event_id: str
    device_id: str
    snapshot_id: str
    timestamp: datetime
    type: str
    severity: str
    title: str
    description: str | None
    details: str | None
    acknowledged: bool


@dataclass
class EvidenceRecord:
    """Запись доказательства."""
    id: str
    snapshot_id: str
    description: str
    contribution: int
    source: str
    details: str | None
    timestamp: datetime | None = None


@dataclass
class CapabilityRecord:
    """Запись возможности устройства."""
    id: str
    snapshot_id: str
    capability: str
    confidence: int | None
    timestamp: datetime | None = None


@dataclass
class DeviceHistory:
    """
    Полная история устройства (ленивая загрузка).
    Поля заполняются только при обращении.
    """
    device_id: str
    mac: str
    first_seen: datetime
    last_seen: datetime
    
    # Ленивые поля
    _snapshots: list[SnapshotRecord] | None = field(default=None, repr=False)
    _observations: list[ObservationRecord] | None = field(default=None, repr=False)
    _events: list[EventRecord] | None = field(default=None, repr=False)
    _evidence: list[EvidenceRecord] | None = field(default=None, repr=False)
    _capabilities: list[CapabilityRecord] | None = field(default=None, repr=False)
    
    # Ссылка на сервис для ленивой загрузки
    _service: Any = field(default=None, repr=False)

    @property
    def snapshots(self) -> list[SnapshotRecord]:
        if self._snapshots is None and self._service:
            self._snapshots = self._service.get_snapshots(self.device_id)
        return self._snapshots or []

    @property
    def observations(self) -> list[ObservationRecord]:
        if self._observations is None and self._service:
            self._observations = self._service.get_observations(self.device_id)
        return self._observations or []

    @property
    def events(self) -> list[EventRecord]:
        if self._events is None and self._service:
            self._events = self._service.get_events(self.device_id)
        return self._events or []

    @property
    def evidence(self) -> list[EvidenceRecord]:
        if self._evidence is None and self._service:
            self._evidence = self._service.get_evidence(self.device_id)
        return self._evidence or []

    @property
    def capabilities(self) -> list[CapabilityRecord]:
        if self._capabilities is None and self._service:
            self._capabilities = self._service.get_capabilities(self.device_id)
        return self._capabilities or []
