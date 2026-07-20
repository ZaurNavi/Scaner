#!/usr/bin/env python3
"""
FingerprintContext — входной объект для Pipeline.
ES-1.8.2: Pipeline принимает единый объект, а не набор параметров.

Это позволяет использовать Pipeline для:
- Replay
- Offline Scan
- PCAP
- Import
- Tests
без изменения API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from models import Device
from configuration import ConfigurationManager


@dataclass(frozen=True)
class FingerprintContext:
    """
    Входной контекст для FingerprintPipeline.
    
    ES-1.8.2:
    - Immutable (frozen=True)
    - Содержит все необходимые данные для Pipeline
    - Pipeline не принимает devices напрямую
    """
    ips: tuple  # Immutable tuple вместо list
    devices: tuple  # Immutable tuple вместо list
    configuration: ConfigurationManager
    scan_timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Валидация после создания."""
        if not self.ips:
            raise ValueError("FingerprintContext.ips cannot be empty")
        if not self.devices:
            raise ValueError("FingerprintContext.devices cannot be empty")
        if len(self.ips) != len(self.devices):
            raise ValueError(
                f"FingerprintContext.ips length ({len(self.ips)}) "
                f"must match devices length ({len(self.devices)})"
            )
    
    @classmethod
    def create(
        cls,
        ips: List[str],
        devices: List[Device],
        configuration: ConfigurationManager,
        scan_timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FingerprintContext:
        """
        Фабричный метод для создания FingerprintContext.
        
        Преобразует list в tuple для immutability.
        """
        return cls(
            ips=tuple(ips),
            devices=tuple(devices),
            configuration=configuration,
            scan_timestamp=scan_timestamp or datetime.now(),
            metadata=metadata or {}
        )
