#!/usr/bin/env python3
"""
NTP Collector — опрос NTP-сервера устройства (UDP 123).
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

import socket
import struct
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


class NTPCollector(ActiveCollector):
    PRIORITY = 58
    RELIABILITY = 75

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.ntp.timeout", 1.0)
        self.port = self.config.get("collector.ntp.port", 123)

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

        ntp_data = self._query_ntp(device.ip)
        if ntp_data:
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="NTP",
                device_id=device.ip,
                attribute="ntp_info",
                value=ntp_data  # Dict разрешён в NormalizedValue
            )]
        return []

    def _query_ntp(self, ip: str) -> dict | None:
        try:
            # NTP Client Request (Mode 3)
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
                    "stratum": stratum,
                    "reference_id": ref_id_str,
                    "poll_interval": t[2] >> 24 & 0xFF,
                    "precision": t[3] >> 24 & 0xFF if (t[3] >> 24 & 0x80) else t[3] >> 24,
                }
            return None
        except Exception:
            return None
