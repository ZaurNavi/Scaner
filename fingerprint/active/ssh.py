#!/usr/bin/env python3
from __future__ import annotations
import socket, time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set
from configuration import ConfigurationManager

class SSHCollector(ActiveCollector):
    PRIORITY = 51
    RELIABILITY = 90
    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.ssh.timeout", 1.0)
        self.workers = self.config.get("collector.ssh.workers", 64)
        self.port = self.config.get("collector.ssh.port", 22)

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()
        cached = cache_get(device.ip, "ssh")
        if cached: return FingerprintResult(**cached, source="ssh", elapsed_ms=0.0)
        if not self.is_available(device):
            return FingerprintResult(source="ssh", raw_data={"responded": False}, elapsed_ms=(time.time() - start_time) * 1000)
        
        banner = self._get_banner(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000
        result = FingerprintResult(source="ssh", raw_data={"responded": True, "banner": banner} if banner else {"responded": False, "reason": "no_banner"}, elapsed_ms=elapsed_ms)
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
        except Exception: return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        results = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in devices}
            for future in as_completed(futures):
                ip = futures[future]
                try: results[ip] = future.result()
                except Exception: results[ip] = FingerprintResult(source="ssh", elapsed_ms=0.0)
        return results
