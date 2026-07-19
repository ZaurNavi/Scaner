#!/usr/bin/env python3
from __future__ import annotations
import time, mmh3, requests
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set
from configuration import ConfigurationManager

class FaviconCollector(ActiveCollector):
    PRIORITY = 76
    RELIABILITY = 85
    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.favicon.timeout", 2.0)
        self.workers = self.config.get("collector.favicon.workers", 32)

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()
        cached = cache_get(device.ip, "favicon")
        if cached: return FingerprintResult(**cached, source="favicon", elapsed_ms=0.0)
        if not self.is_available(device):
            return FingerprintResult(source="favicon", raw_data={"responded": False, "reason": "device_unavailable"}, elapsed_ms=(time.time() - start_time) * 1000)
        
        favicon_data = self._get_favicon_hash(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000
        result = FingerprintResult(source="favicon", raw_data=favicon_data or {"responded": False, "reason": "no_favicon_or_timeout"}, elapsed_ms=elapsed_ms, capabilities=["supports_favicon"] if favicon_data else [])
        cache_set(device.ip, "favicon", asdict(result))
        return result

    def _get_favicon_hash(self, ip: str) -> dict | None:
        for scheme in ["http", "https"]:
            try:
                response = requests.get(f"{scheme}://{ip}/favicon.ico", timeout=self.timeout, verify=False, allow_redirects=True)
                if response.status_code == 200 and len(response.content) > 0:
                    return {"responded": True, "scheme": scheme, "mmh3_hash": mmh3.hash(response.content), "size_bytes": len(response.content)}
            except Exception: continue
        return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        targets = devices
        if context and "tcp" in context:
            tcp_ctx = context["tcp"]
            targets = [d for d in devices if tcp_ctx.get(d.ip) and any(str(p) in tcp_ctx[d.ip].raw_data.get("open_ports", []) for p in [80, 443, 8080, 8443])]
        results = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                ip = futures[future]
                try: results[ip] = future.result()
                except Exception: results[ip] = FingerprintResult(source="favicon", elapsed_ms=0.0)
        return results
