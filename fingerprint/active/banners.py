#!/usr/bin/env python3
"""
Service Banners Collector — чтение баннеров с портов IoT и специфичных сервисов.
Порты: 21 (FTP), 23 (Telnet), 554 (RTSP), 1883 (MQTT), 5060 (SIP).
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


class BannersCollector(ActiveCollector):
    PRIORITY = 55
    RELIABILITY = 85

    def __init__(self):
        super().__init__(timeout=1.0)
        self.workers = 64
        # Порты и ожидаемые начальные байты для идентификации
        self.ports_to_check = [
            (21, b"220"),      # FTP
            (23, b""),         # Telnet (любой ответ)
            (554, b"RTSP"),    # RTSP (IP-камеры)
            (5060, b"SIP"),    # SIP (Телефония)
        ]

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        cached = cache_get(device.ip, "banners")
        if cached:
            return FingerprintResult(**cached, source="banners", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(
                source="banners",
                raw_data={"responded": False, "reason": "device_unavailable"},
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        banners_data = self._get_banners(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if banners_data:
            result = FingerprintResult(
                source="banners",
                raw_data=banners_data,
                elapsed_ms=elapsed_ms,
                capabilities=["supports_banners"]
            )
        else:
            result = FingerprintResult(
                source="banners",
                raw_data={"responded": False, "reason": "no_banners_found"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "banners", asdict(result))
        return result

    def _get_banners(self, ip: str) -> dict | None:
        found_banners = {}
        
        for port, expected_prefix in self.ports_to_check:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                sock.connect((ip, port))
                
                # Для некоторых сервисов нужно отправить минимальный запрос, чтобы получить ответ
                if port == 5060:
                    sock.send(b"OPTIONS sip:info@{} SIP/2.0\r\n\r\n".format(ip).encode())
                elif port == 1883:
                    # Минимальный MQTT CONNECT packet (будет закрыт, но иногда дает инфо)
                    sock.send(b"\x10\x16\x00\x04MQTT\x04\x02\x00\x3c\x00\x0bScannerTest")
                
                response = sock.recv(256)
                sock.close()

                if response:
                    banner_str = response.decode('utf-8', errors='ignore').strip().replace('\r', '').replace('\n', ' ')
                    if not expected_prefix or banner_str.startswith(expected_prefix.decode('utf-8', errors='ignore')):
                        found_banners[str(port)] = banner_str[:100]  # Ограничиваем длину

            except (socket.timeout, socket.error, ConnectionResetError):
                continue
            except Exception:
                continue

        return {"responded": True, "banners": found_banners} if found_banners else None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        """
        Оптимизация: запускаем только если в TCP context есть открытые порты из нашего списка.
        """
        targets = devices
        if context and "tcp" in context:
            tcp_ctx = context["tcp"]
            target_ports = {21, 23, 554, 1883, 5060}
            filtered_targets = []
            for d in devices:
                tcp_res = tcp_ctx.get(d.ip)
                if tcp_res and tcp_res.raw_data.get("open_ports"):
                    ports = tcp_res.raw_data.get("open_ports", [])
                    # Проверяем пересечение портов
                    if any(str(p) in ports or int(p) in ports for p in target_ports for p in [p]):
                        filtered_targets.append(d)
            targets = filtered_targets if filtered_targets else devices

        results: dict[str, FingerprintResult] = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    results[ip] = future.result()
                except Exception:
                    results[ip] = FingerprintResult(source="banners", elapsed_ms=0.0)
        return results
