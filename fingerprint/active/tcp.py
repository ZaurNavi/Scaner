#!/usr/bin/env python3
"""
TCP Collector — сканирование портов.
v1.7.1: Интеграция с Configuration Layer.
"""

from __future__ import annotations

import socket
import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set
from configuration import ConfigurationManager


class TCPCollector(ActiveCollector):
    PRIORITY = 50
    RELIABILITY = 60

    def __init__(self, configuration: ConfigurationManager, fast: bool = False):
        super().__init__(configuration)
        self.fast = fast
        self.timeout = self.config.get("collector.tcp.timeout", 1.0)
        self.max_connections = self.config.get("collector.tcp.max_connections", 32)
        
        core_ports = [int(x) for x in self.config.get("collector.tcp.core_ports", "22,53,80,443,445,554,631,9100").split(",")]
        optional_ports = [int(x) for x in self.config.get("collector.tcp.optional_ports", "81,139,8080,8081,8443,8291,8728,3389,5357,8008,8009,32400,5000,5001").split(",")]
        self.ports = core_ports if fast else core_ports + optional_ports

    def _scan_port(self, ip: str, port: int) -> tuple[int, str, float]:
        start = time.time()
        try:
            sock = socket.create_connection((ip, port), timeout=self.timeout)
            latency = (time.time() - start) * 1000
            sock.close()
            return port, "open", latency
        except socket.timeout:
            return port, "filtered", 0. if self.fast else 0.0
        except (ConnectionRefusedError, socket.error, OSError):
            return port, "closed", 0.0

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()
        cached = cache_get(device.ip, "tcp")
        if cached:
            return FingerprintResult(**cached, source="tcp", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(source="tcp", elapsed_ms=(time.time() - start_time) * 1000)

        services: dict[int, dict] = {}
        workers = min(self.max_connections, len(self.ports))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self._scan_port, device.ip, port): port for port in self.ports}
            for future in as_completed(futures):
                port, state, latency = future.result()
                services[port] = {"state": state, "latency_ms": round(latency, 2)}

        services = dict(sorted(services.items()))
        open_ports = [p for p, info in services.items() if info["state"] == "open"]
        elapsed_ms = (time.time() - start_time) * 1000

        result = FingerprintResult(
            source="tcp", services=services, ports=open_ports,
            raw_data={"fast_mode": self.fast, "ports_scanned": len(self.ports), "ports_open": len(open_ports)},
            elapsed_ms=elapsed_ms,
        )
        cache_set(device.ip, "tcp", asdict(result))
        return result
