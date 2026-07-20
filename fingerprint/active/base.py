#!/usr/bin/env python3
"""
Базовый интерфейс для активных коллекторов.
ES-1.8.3: Возвращает строго List[Observation].
Legacy-класс FingerprintResult удалён.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from models import Device
from configuration import ConfigurationManager


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
    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает List[Observation]."""
        pass

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> list:
        """ES-1.8.3: Возвращает List[Observation] для всех устройств."""
        if not devices:
            return []
        targets = [d for d in devices if self.is_available(d)]
        if not targets:
            return []

        from concurrent.futures import ThreadPoolExecutor, as_completed
        all_observations = []
        workers = min(self.workers, len(targets))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                try:
                    all_observations.extend(future.result())
                except Exception:
                    pass
        return all_observations

    @property
    def source_name(self) -> str:
        return self.__class__.__name__.replace("Collector", "").lower()
