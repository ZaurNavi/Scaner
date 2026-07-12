#!/usr/bin/env python3
"""
TCP Collector — сканирование портов.

Архитектура:
- Только собирает сырые данные (открытые/закрытые порты, latency)
- НЕ определяет тип устройства — это делает Correlation Engine
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


# ---------------------------------------------------------
# Список портов для сканирования
# ---------------------------------------------------------

CORE_PORTS = (
    22,     # SSH
    53,     # DNS
    80,     # HTTP
    443,    # HTTPS
    445,    # SMB
    554,    # RTSP (IP Camera)
    631,    # IPP (Printer)
    9100,   # Printer (RAW)
)

OPTIONAL_PORTS = (
    81,     # HTTP alt
    139,    # NetBIOS
    8080,   # HTTP proxy
    8081,   # HTTP alt
    8443,   # HTTPS alt
    8291,   # MikroTik Winbox
    8728,   # MikroTik API
    3389,   # RDP (Windows)
    5357,   # WSDAPI (Windows)
    8008,   # Chromecast
    8009,   # Chromecast
    32400,  # Plex
    5000,   # Synology
    5001,   # Synology
)

ALL_PORTS = CORE_PORTS + OPTIONAL_PORTS


class TCPCollector(ActiveCollector):
    """
    Сканирует TCP-порты для сбора сырых данных.
    НЕ интерпретирует результаты — только собирает факты.
    """

    PRIORITY = 50
    RELIABILITY = 60

    def __init__(self, fast: bool = False):
        super().__init__(timeout=Fingerprint.TCP_TIMEOUT)
        self.ports = CORE_PORTS if fast else ALL_PORTS
        self.fast = fast

    def _scan_port(self, ip: str, port: int) -> tuple[int, str, float]:
        """
        Проверяет один порт.
        Возвращает (port, state, latency_ms).
        """
        start = time.time()
        try:
            sock = socket.create_connection((ip, port), timeout=self.timeout)
            latency = (time.time() - start) * 1000
            sock.close()
            return port, "open", latency
        except socket.timeout:
            return port, "filtered", 0.0
        except ConnectionRefusedError:
            return port, "closed", 0.0
        except (socket.error, OSError):
            return port, "closed", 0.0

    def collect(self, device: Device) -> FingerprintResult:
        """
        Сканирует все порты для одного устройства.
        Возвращает ТОЛЬКО сырые данные — без device_type, confidence, reason.
        """
        start_time = time.time()

        # Проверка кэша
        cached = cache_get(device.ip, "tcp")
        if cached:
            return FingerprintResult(**cached, source="tcp", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(
                source="tcp",
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        services: dict[int, dict] = {}
        workers = min(Fingerprint.TCP_MAX_CONNECTIONS_PER_HOST, len(self.ports))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._scan_port, device.ip, port): port
                for port in self.ports
            }

            for future in as_completed(futures):
                port, state, latency = future.result()
                services[port] = {
                    "state": state,
                    "latency_ms": round(latency, 2),
                }

        # Сортируем по номеру порта
        services = dict(sorted(services.items()))
        open_ports = [p for p, info in services.items() if info["state"] == "open"]

        elapsed_ms = (time.time() - start_time) * 1000

        # Возвращаем ТОЛЬКО сырые данные — без интерпретации
        result = FingerprintResult(
            source="tcp",
            services=services,
            ports=open_ports,
            raw_data={
                "fast_mode": self.fast,
                "ports_scanned": len(self.ports),
                "ports_open": len(open_ports),
            },
            elapsed_ms=elapsed_ms,
        )

        # Сохранение в кэш
        cache_set(device.ip, "tcp", asdict(result))

        return result
