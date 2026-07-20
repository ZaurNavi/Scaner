#!/usr/bin/env python3
"""
NetBIOS Name Collector — получение имени компьютера через UDP 137.
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

import socket
import struct
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


class NetBIOSCollector(ActiveCollector):
    PRIORITY = 47
    RELIABILITY = 80

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.netbios.timeout", 1.0)
        self.workers = self.config.get("collector.netbios.workers", 32)

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

        netbios_data = self._query_netbios(device.ip)
        if netbios_data:
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="NetBIOS",
                device_id=device.ip,
                attribute="netbios_info",
                value=netbios_data
            )]
        return []

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> list:
        """ES-1.8.3: scan теперь возвращает List[Observation] для всех устройств."""
        all_observations = []
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in devices}
            for future in as_completed(futures):
                try:
                    all_observations.extend(future.result())
                except Exception:
                    pass
        return all_observations

    def _query_netbios(self, ip: str) -> dict | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            packet = struct.pack('>HHHHHH', 0x1234, 0x0000, 1, 0, 0, 0) + b'\x20CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\x00' + struct.pack('>HH', 0x0021, 0x0001)
            sock.sendto(packet, (ip, 137))
            data, addr = sock.recvfrom(1024)
            sock.close()
            
            if len(data) >= 12:
                offset = 12
                if offset < len(data):
                    name_length = data[offset]
                    offset += 1
                    if name_length > 0 and offset + name_length <= len(data):
                        return {
                            "responded": True, 
                            "computer_name": self._decode_netbios_name(data[offset:offset + name_length]), 
                            "ip": ip
                        }
            return None
        except Exception:
            return None

    def _decode_netbios_name(self, encoded: bytes) -> str:
        try:
            decoded = []
            for i in range(0, len(encoded), 2):
                if i + 1 < len(encoded):
                    char_code = ((encoded[i] - 0x41) << 4) | (encoded[i + 1] - 0x41)
                    if 32 <= char_code <= 126:
                        decoded.append(chr(char_code))
            return ''.join(decoded).rstrip()
        except Exception:
            return ""
