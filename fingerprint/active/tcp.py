#!/usr/bin/env python3
from __future__ import annotations
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory, ObservationCategory

CORE_PORTS = (22, 53, 80, 443, 445, 554, 631, 9100)
OPTIONAL_PORTS = (81, 139, 8080, 8081, 8443, 8291, 8728, 3389, 5357, 8008, 8009, 32400, 5000, 5001)

class TCPCollector(ActiveCollector):
    PRIORITY = 50
    RELIABILITY = 60

    def __init__(self, configuration: ConfigurationManager, fast: bool = False):
        super().__init__(configuration)
        self.fast = fast
        self.timeout = self.config.get("collector.tcp.timeout", 1.0)
        self.max_connections = self.config.get("collector.tcp.max_connections", 32)
        
        core = tuple(int(x) for x in self.config.get("collector.tcp.core_ports", ",".join(map(str, CORE_PORTS))).split(",") if x.strip())
        optional = tuple(int(x) for x in self.config.get("collector.tcp.optional_ports", ",".join(map(str, OPTIONAL_PORTS))).split(",") if x.strip())
        self.ports = core if fast else core + optional

    def _scan_port(self, ip: str, port: int) -> int | None:
        try:
            sock = socket.create_connection((ip, port), timeout=self.timeout)
            sock.close()
            return port
        except (socket.timeout, ConnectionRefusedError, socket.error, OSError):
            return None

    # ES-1.8.3: collect возвращает List[Observation]
    def collect(self, device: Device) -> list:
        if not self.is_available(device): return []

        open_ports = []
        workers = min(self.max_connections, len(self.ports))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self._scan_port, device.ip, port): port for port in self.ports}
            for future in as_completed(futures):
                port = future.result()
                if port is not None:
                    open_ports.append(port)

        if open_ports:
            return [ObservationFactory.create_open_ports(
                collector_id=self.source_name, protocol="TCP", device_id=device.ip, ports=open_ports
            )]
        return []
