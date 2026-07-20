#!/usr/bin/env python3
"""
DNS-SD (Bonjour Service Discovery) Collector.
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


class DnsSdCollector(ActiveCollector):
    PRIORITY = 65
    RELIABILITY = 80

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.dns_sd.timeout", 1.5)
        self.workers = self.config.get("collector.dns_sd.workers", 32)
        self.services = [
            "_airplay._tcp.local", "_googlecast._tcp.local", "_ipp._tcp.local", 
            "_printer._tcp.local", "_raop._tcp.local", "_http._tcp.local"
        ]

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

        sd_data = self._query_dns_sd(device.ip)
        if sd_data and sd_data.get("services"):
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="DNS-SD",
                device_id=device.ip,
                attribute="dns_sd_services",
                value=sd_data["services"]  # List разрешён в NormalizedValue
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

    def _query_dns_sd(self, ip: str) -> dict | None:
        found_services = []
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.settimeout(self.timeout)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            
            for service in self.services:
                query = b'\x12\x34\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00'
                for part in service.split('.'):
                    query += bytes([len(part)]) + part.encode('utf-8')
                query += b'\x00\x00\x0c\x00\x01'
                sock.sendto(query, ("224.0.0.251", 5353))
            
            start = time.time()
            while time.time() - start < self.timeout:
                try:
                    data, addr = sock.recvfrom(1024)
                    if addr[0] == ip:
                        for service in self.services:
                            if service.replace('.local', '').encode('utf-8') in data and service not in found_services:
                                found_services.append(service)
                except socket.timeout:
                    break
            sock.close()
        except Exception:
            pass
            
        return {"responded": True, "services": found_services} if found_services else None
