#!/usr/bin/env python3
"""
Favicon Hash Collector — загрузка favicon.ico и вычисление mmh3 хэша.
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

import mmh3
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


class FaviconCollector(ActiveCollector):
    PRIORITY = 76
    RELIABILITY = 85

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.favicon.timeout", 2.0)
        self.workers = self.config.get("collector.favicon.workers", 32)

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

        favicon_data = self._get_favicon_hash(device.ip)
        if favicon_data:
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="HTTP",
                device_id=device.ip,
                attribute="favicon_hash",
                value=favicon_data
            )]
        return []

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> list:
        """ES-1.8.3: scan теперь возвращает List[Observation] для всех устройств."""
        all_observations = []
        targets = devices
        if context and "tcp" in context:
            tcp_ctx = context["tcp"]
            targets = [d for d in devices if tcp_ctx.get(d.ip) and any(str(p) in tcp_ctx[d.ip].raw_data.get("open_ports", []) for p in [80, 443, 8080, 8443])]

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                try:
                    all_observations.extend(future.result())
                except Exception:
                    pass
        return all_observations

    def _get_favicon_hash(self, ip: str) -> dict | None:
        for scheme in ["http", "https"]:
            try:
                response = requests.get(f"{scheme}://{ip}/favicon.ico", timeout=self.timeout, verify=False, allow_redirects=True)
                if response.status_code == 200 and len(response.content) > 0:
                    return {
                        "responded": True,
                        "scheme": scheme,
                        "mmh3_hash": mmh3.hash(response.content),
                        "size_bytes": len(response.content)
                    }
            except Exception:
                continue
        return None
