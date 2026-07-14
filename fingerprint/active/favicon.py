#!/usr/bin/env python3
"""
Favicon Hash Collector — загрузка favicon.ico и вычисление mmh3 хэша.
Позволяет точно идентифицировать веб-интерфейсы (Mikrotik, Ubiquiti, TrueNAS и т.д.).
"""

from __future__ import annotations

import time
import mmh3
import requests
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class FaviconCollector(ActiveCollector):
    PRIORITY = 76  # После HTTP и HTTPS
    RELIABILITY = 85

    def __init__(self):
        super().__init__(timeout=2.0)
        self.workers = 32

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        cached = cache_get(device.ip, "favicon")
        if cached:
            return FingerprintResult(**cached, source="favicon", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(
                source="favicon",
                raw_data={"responded": False, "reason": "device_unavailable"},
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        favicon_data = self._get_favicon_hash(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if favicon_data:
            result = FingerprintResult(
                source="favicon",
                raw_data=favicon_data,
                elapsed_ms=elapsed_ms,
                capabilities=["supports_favicon"]
            )
        else:
            result = FingerprintResult(
                source="favicon",
                raw_data={"responded": False, "reason": "no_favicon_or_timeout"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "favicon", asdict(result))
        return result

    def _get_favicon_hash(self, ip: str) -> dict | None:
        # Пробуем HTTP и HTTPS
        for scheme in ["http", "https"]:
            try:
                url = f"{scheme}://{ip}/favicon.ico"
                # Игнорируем ошибки SSL для самоподписанных сертификатов
                response = requests.get(url, timeout=self.timeout, verify=False, allow_redirects=True)
                
                if response.status_code == 200 and len(response.content) > 0:
                    # Вычисляем mmh3 hash от байтов
                    hash_val = mmh3.hash(response.content)
                    return {
                        "responded": True,
                        "scheme": scheme,
                        "mmh3_hash": hash_val,
                        "size_bytes": len(response.content)
                    }
            except Exception:
                continue
        return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        # Запускаем только для устройств, у которых открыт 80 или 443 порт
        targets = devices
        if context and "tcp" in context:
            tcp_ctx = context["tcp"]
            targets = [
                d for d in devices 
                if tcp_ctx.get(d.ip) and any(str(p) in tcp_ctx[d.ip].raw_data.get("open_ports", []) for p in [80, 443, 8080, 8443])
            ]

        results: dict[str, FingerprintResult] = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    results[ip] = future.result()
                except Exception:
                    results[ip] = FingerprintResult(source="favicon", elapsed_ms=0.0)
        return results
