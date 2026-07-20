#!/usr/bin/env python3
"""
Service Banners Collector — чтение баннеров с широкого спектра портов.
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


class BannersCollector(ActiveCollector):
    PRIORITY = 55
    RELIABILITY = 85

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.banners.timeout", 1.0)
        self.workers = self.config.get("collector.banners.workers", 64)
        self.ports_to_check = [
            (21, b"220"), (23, b""), (25, b"220"), (110, b"+OK"), 
            (143, b"* OK"), (554, b"RTSP"), (1883, b""), 
            (3389, b"\x03\x00\x00"), (5900, b"RFB"), 
            (6379, b"-ERR"), (9200, b"\"name\"")
        ]

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

        banners_data = self._get_banners(device.ip)
        if banners_data:
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="TCP",
                device_id=device.ip,
                attribute="service_banners",
                value=banners_data
            )]
        return []

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> list:
        """ES-1.8.3: scan теперь возвращает List[Observation] для всех устройств."""
        all_observations = []
        targets = devices
        if context and "tcp" in context:
            tcp_ctx = context["tcp"]
            target_ports = {21, 23, 25, 110, 143, 554, 1883, 3389, 5900, 6379, 9200}
            targets = [d for d in devices if tcp_ctx.get(d.ip) and any(str(p) in tcp_ctx[d.ip].raw_data.get("open_ports", []) or int(p) in tcp_ctx[d.ip].raw_data.get("open_ports", []) for p in target_ports)]

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                try:
                    all_observations.extend(future.result())
                except Exception:
                    pass
        return all_observations

    def _get_banners(self, ip: str) -> dict | None:
        found_banners = {}
        for port, expected_prefix in self.ports_to_check:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                sock.connect((ip, port))

                if port == 1883:
                    sock.send(b"\x10\x16\x00\x04MQTT\x04\x02\x00\x3c\x00\x0bScannerTest")
                elif port == 9200:
                    sock.send(b"GET / HTTP/1.0\r\n\r\n")
                elif port == 3389:
                    sock.send(b"\x03\x00\x00\x13\x0e\xe0\x00\x00\x00\x00\x00\x01\x00\x08\x00\x03\x00\x00\x00")

                response = sock.recv(512)
                sock.close()

                if response:
                    banner_str = response.decode('utf-8', errors='ignore').strip().replace('\r', '').replace('\n', ' ')
                    if not expected_prefix or banner_str.encode('utf-8', errors='ignore').startswith(expected_prefix):
                        found_banners[str(port)] = banner_str[:150]
            except Exception:
                continue

        return {"responded": True, "banners": found_banners} if found_banners else None
