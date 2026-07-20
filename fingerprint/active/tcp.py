#!/usr/bin/env python3
"""
TCP Collector — сканирование портов.
v1.7.1: Интеграция с Configuration Layer.
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""

from __future__ import annotations

import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


# v1.7.1: Экспортируемые константы для обратной совместимости (Category B — Domain Constants)
CORE_PORTS = (22, 53, 80, 443, 445, 554, 631, 9100)
OPTIONAL_PORTS = (81, 139, 8080, 8081, 8443, 8291, 8728, 3389, 5357, 8008, 8009, 32400, 5000, 5001)
ALL_PORTS = CORE_PORTS + OPTIONAL_PORTS  # ← ЭТА СТРОКА БЫЛА ОТСУТСТВУЕТ


class TCPCollector(ActiveCollector):
    PRIORITY = 50
    RELIABILITY = 60

    def __init__(self, configuration: ConfigurationManager, fast: bool = False):
        super().__init__(configuration)
        self.fast = fast
        self.timeout = self.config.get("collector.tcp.timeout", 1.0)
        self.max_connections = self.config.get("collector.tcp.max_connections", 32)

        # v1.7.1: Читаем порты из Configuration Layer (если настроено)
        core_ports_str = self.config.get("collector.tcp.core_ports", "")
        optional_ports_str = self.config.get("collector.tcp.optional_ports", "")

        if core_ports_str:
            core = tuple(int(x) for x in core_ports_str.split(",") if x.strip())
        else:
            core = CORE_PORTS

        if optional_ports_str:
            optional = tuple(int(x) for x in optional_ports_str.split(",") if x.strip())
        else:
            optional = OPTIONAL_PORTS

        self.ports = core if fast else core + optional

    def _scan_port(self, ip: str, port: int) -> int | None:
        try:
            sock = socket.create_connection((ip, port), timeout=self.timeout)
            sock.close()
            return port
        except (socket.timeout, ConnectionRefusedError, socket.error, OSError):
            return None

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

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

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> list:
        """ES-1.8.3: scan теперь возвращает List[Observation] для всех устройств."""
        all_observations = []
        targets = devices
        if context and "tcp" in context:
            tcp_ctx = context["tcp"]
            target_ports = set(self.ports)
            targets = [d for d in devices if tcp_ctx.get(d.ip) and any(str(p) in tcp_ctx[d.ip].raw_data.get("open_ports", []) or int(p) in tcp_ctx[d.ip].raw_data.get("open_ports", []) for p in target_ports)]

        for device in targets:
            if self.is_available(device):
                all_observations.extend(self.collect(device))
        return all_observations
