#!/usr/bin/env python3
"""
NTP Collector — опрос NTP-сервера устройства (UDP 123).
Может выдать stratum, reference ID и версию ПО (особенно у сетевого оборудования).
"""

from __future__ import annotations

import socket
import struct
import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Fingerprint
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class NTPCollector(ActiveCollector):
    PRIORITY = 58
    RELIABILITY = 75

    def __init__(self):
        super().__init__(timeout=1.0)
        self.workers = 32
        self.port = 123

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        cached = cache_get(device.ip, "ntp")
        if cached:
            return FingerprintResult(**cached, source="ntp", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(
                source="ntp",
                raw_data={"responded": False, "reason": "device_unavailable"},
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        ntp_data = self._query_ntp(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if ntp_data:
            result = FingerprintResult(
                source="ntp",
                raw_data=ntp_data,
                elapsed_ms=elapsed_ms,
                capabilities=["supports_ntp"]
            )
        else:
            result = FingerprintResult(
                source="ntp",
                raw_data={"responded": False, "reason": "no_ntp_response"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "ntp", asdict(result))
        return result

    def _query_ntp(self, ip: str) -> dict | None:
        try:
            # NTP Client Request (Mode 3)
            # LI=0, VN=3, Mode=3, Stratum=0, Poll=0, Precision=0
            packet = b'\x1b' + 47 * b'\0'
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            sock.sendto(packet, (ip, self.port))
            data, _ = sock.recvfrom(256)
            sock.close()

            if len(data) >= 48:
                # Парсим базовые поля NTP-ответа
                t = struct.unpack("!12I", data[:48])
                stratum = t[1] >> 24 & 0xFF
                # Reference ID (часто содержит версию или имя, если stratum <= 2)
                ref_id = data[12:16]
                try:
                    ref_id_str = ref_id.decode('ascii', errors='ignore').strip()
                except Exception:
                    ref_id_str = ref_id.hex()

                return {
                    "responded": True,
                    "stratum": stratum,
                    "reference_id": ref_id_str,
                    "poll_interval": t[2] >> 24 & 0xFF,
                    "precision": t[3] >> 24 & 0xFF if (t[3] >> 24 & 0x80) else t[3] >> 24,
                }
            return None

        except (socket.timeout, socket.error, ConnectionResetError):
            return None
        except Exception:
            return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        results: dict[str, FingerprintResult] = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in devices}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    results[ip] = future.result()
                except Exception:
                    results[ip] = FingerprintResult(source="ntp", elapsed_ms=0.0)
        return results
