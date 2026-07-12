#!/usr/bin/env python3
"""
Базовый интерфейс для активных коллекторов.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time

from config import Detection
from models import Device


@dataclass(frozen=True)
class FingerprintResult:
    hostname: str = ""
    model: str = ""
    os: str = ""
    device_type: str = ""
    vendor: str = ""
    reason: str = ""
    services: dict = field(default_factory=dict)
    ports: list[int] = field(default_factory=list)
    ttl: int | None = None
    latency_ms: float | None = None
    mac_vendor: str = ""
    banner: str = ""
    server: str = ""
    confidence: int = 0
    elapsed_ms: float = 0.0
    raw_data: dict = field(default_factory=dict)
    source: str = ""


class ActiveCollector(ABC):
    PRIORITY: int = 0
    RELIABILITY: int = 0

    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout

    def is_available(self, device: Device) -> bool:
        ip = device.ip
        if ip.startswith("127."): return False
        if ip == "255.255.255.255" or ip.endswith(".255"): return False
        first_octet = int(ip.split(".")[0])
        if 224 <= first_octet <= 239: return False
        if ip in Detection.EXCLUDED_IPS: return False
        return True

    @abstractmethod
    def collect(self, device: Device) -> FingerprintResult:
        pass

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        """
        context: словарь с результатами предыдущих стадий (tcp, mdns, и т.д.)
        kwargs: для будущего расширения
        """
        if not devices:
            return {}
        targets = [d for d in devices if self.is_available(d)]
        if not targets:
            return {}

        from concurrent.futures import ThreadPoolExecutor, as_completed
        results: dict[str, FingerprintResult] = {}
        workers = min(32, len(targets))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self.collect, d): d for d in targets}
            for future in as_completed(futures):
                device = futures[future]
                try:
                    results[device.ip] = future.result()
                except Exception:
                    results[device.ip] = FingerprintResult(source=self.source_name, elapsed_ms=0.0)
        return results

    @property
    def source_name(self) -> str:
        return self.__class__.__name__.replace("Collector", "").lower()
