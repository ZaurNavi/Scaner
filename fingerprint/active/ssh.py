#!/usr/bin/env python3
"""
SSH Banner Collector — чтение баннера с порта 22.
"""

from __future__ import annotations

import socket
import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Fingerprint
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class SSHCollector(ActiveCollector):
    PRIORITY = 51
    RELIABILITY = 90

    def __init__(self):
        super().__init__(timeout=1.0)
        self.workers = 64
        self.port = 22

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        cached = cache_get(device.ip, "ssh")
        if cached:
            return FingerprintResult(**cached, source="ssh", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(source="ssh", raw_data={"responded": False}, elapsed_ms=(time.time() - start_time) * 1000)

        banner = self._get_banner(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if banner:
            result = FingerprintResult(
                source="ssh",
                raw_data={"responded": True, "banner": banner},
                elapsed_ms=elapsed_ms,
            )
        else:
            result = FingerprintResult(
                source="ssh",
                raw_data={"responded": False, "reason": "no_banner"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "ssh", asdict(result))
        return result

    def _get_banner(self, ip: str) -> str | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, self.port))
            banner = sock.recv(128).decode('utf-8', errors='ignore').strip()
            sock.close()
            return banner if banner.startswith("SSH-") else None
        except (socket.timeout, socket.error, ConnectionResetError):
            return None
        except Exception:
            return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        results: dict[str, FingerprintResult] = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, device): device.ip for device in devices}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    results[ip] = future.result()
                except Exception:
                    results[ip] = FingerprintResult(source="ssh", elapsed_ms=0.0)
        return results
