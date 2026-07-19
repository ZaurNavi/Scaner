#!/usr/bin/env python3
"""
Базовый интерфейс для активных коллекторов.
v1.7.1: Интеграция с Configuration Layer через Dependency Injection.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from typing import List
import time

from models import Device
from configuration import ConfigurationManager


@dataclass(frozen=True)
class FingerprintResult:
    hostname: str = ""
    model: str = ""
    os: str = ""
    device_type: str = "UNKNOWN"
    vendor: str = "Unknown"
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
    capabilities: list[str] = field(default_factory=list)


class ActiveCollector(ABC):
    PRIORITY: int = 0
    RELIABILITY: int = 0

    def __init__(self, configuration: ConfigurationManager):
        self.config = configuration
        self.timeout = self.config.get("collector.default.timeout", 2.0)
        self.workers = self.config.get("collector.default.workers", 32)

    def is_available(self, device: Device) -> bool:
        ip = device.ip
        if ip.startswith("127."): return False
        if ip == "255.255.255.255" or ip.endswith(".255"): return False
        first_octet = int(ip.split(".")[0])
        if 224 <= first_octet <= 239: return False
        
        excluded_ips_str = self.config.get("collector.detection.excluded_ips", "")
        excluded_ips = [x.strip() for x in excluded_ips_str.split(",") if x.strip()]
        if ip in excluded_ips: return False
        
        return True

    @abstractmethod
    def collect(self, device: Device) -> FingerprintResult:
        pass

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        if not devices:
            return {}
        targets = [d for d in devices if self.is_available(d)]
        if not targets:
            return {}

        from concurrent.futures import ThreadPoolExecutor, as_completed
        results: dict[str, FingerprintResult] = {}
        workers = min(self.workers, len(targets))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self.collect, d): d for d in targets}
            for future in as_completed(futures):
                device = futures[future]
                try:
                    res = future.result()

                    if res.raw_data.get("responded"):
                        new_caps = list(res.capabilities)
                        cap_name = f"supports_{self.source_name}"
                        if cap_name not in new_caps:
                            new_caps.append(cap_name)

                        res = replace(res, capabilities=new_caps)

                    results[device.ip] = res
                except Exception:
                    results[device.ip] = FingerprintResult(source=self.source_name, elapsed_ms=0.0)
        return results

    @property
    def source_name(self) -> str:
        return self.__class__.__name__.replace("Collector", "").lower()
