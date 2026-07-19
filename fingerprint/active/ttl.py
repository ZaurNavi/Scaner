#!/usr/bin/env python3
from __future__ import annotations
import time
from dataclasses import asdict
from models import Device
from .base import ActiveCollector, FingerprintResult
from .ping import ping
from storage.active_cache import get as cache_get, set as cache_set
from configuration import ConfigurationManager

class TTLCollector(ActiveCollector):
    PRIORITY = 40
    RELIABILITY = 20
    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.ttl.timeout", 1.0)
        self.count = self.config.get("collector.ttl.count", 1)

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()
        cached = cache_get(device.ip, "ttl")
        if cached: return FingerprintResult(**cached, source="ttl", elapsed_ms=0.0)
        if not self.is_available(device):
            return FingerprintResult(source="ttl", elapsed_ms=(time.time() - start_time) * 1000)
        
        ping_result = ping(device.ip, timeout=self.timeout, count=self.count)
        raw_data = {"alive": ping_result.alive, "ttl": ping_result.ttl, "latency_ms": ping_result.latency_ms, "exit_code": ping_result.exit_code, "command": ping_result.command}
        elapsed_ms = (time.time() - start_time) * 1000
        
        result = FingerprintResult(source="ttl", ttl=ping_result.ttl, latency_ms=ping_result.latency_ms, raw_data=raw_data, elapsed_ms=elapsed_ms)
        cache_set(device.ip, "ttl", asdict(result))
        return result
