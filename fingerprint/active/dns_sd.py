#!/usr/bin/env python3
"""
DNS-SD (Bonjour Service Discovery) Collector.
Ищет конкретные сервисы: AirPlay, Google Cast, Printers, HTTP и т.д.
"""

from __future__ import annotations

import socket
import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class DnsSdCollector(ActiveCollector):
    PRIORITY = 65
    RELIABILITY = 80

    def __init__(self):
        super().__init__(timeout=1.5)
        self.workers = 32
        # Список интересных сервисов для поиска
        self.services = [
            "_airplay._tcp.local",
            "_googlecast._tcp.local",
            "_ipp._tcp.local",
            "_printer._tcp.local",
            "_raop._tcp.local",
            "_http._tcp.local",
        ]

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        cached = cache_get(device.ip, "dns_sd")
        if cached:
            return FingerprintResult(**cached, source="dns_sd", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(
                source="dns_sd",
                raw_data={"responded": False, "reason": "device_unavailable"},
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        sd_data = self._query_dns_sd(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if sd_data and sd_data.get("services"):
            result = FingerprintResult(
                source="dns_sd",
                raw_data=sd_data,
                elapsed_ms=elapsed_ms,
                capabilities=["supports_dns_sd"]
            )
        else:
            result = FingerprintResult(
                source="dns_sd",
                raw_data={"responded": False, "reason": "no_services_found"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "dns_sd", asdict(result))
        return result

    def _query_dns_sd(self, ip: str) -> dict | None:
        found_services = []
        
        # Создаем UDP сокет для multicast
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.settimeout(self.timeout)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            
            # Формируем стандартный DNS-SD запрос (упрощенный)
            # Запрашиваем PTR записи для каждого сервиса
            for service in self.services:
                # Простой DNS запрос (Transaction ID: 0x1234, Flags: 0x0000, Questions: 1)
                # Query: service name, type PTR (12), class IN (1)
                query = b'\x12\x34\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00'
                for part in service.split('.'):
                    query += bytes([len(part)]) + part.encode('utf-8')
                query += b'\x00\x00\x0c\x00\x01' # PTR, IN
                
                sock.sendto(query, ("224.0.0.251", 5353))
            
            # Слушаем ответы
            start = time.time()
            while time.time() - start < self.timeout:
                try:
                    data, addr = sock.recvfrom(1024)
                    if addr[0] == ip:
                        # Очень упрощенный парсинг: ищем имена сервисов в ответе
                        for service in self.services:
                            if service.replace('.local', '').encode('utf-8') in data:
                                if service not in found_services:
                                    found_services.append(service)
                except socket.timeout:
                    break
                    
            sock.close()
        except Exception:
            pass

        if found_services:
            return {"responded": True, "services": found_services}
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
                    results[ip] = FingerprintResult(source="dns_sd", elapsed_ms=0.0)
        return results
