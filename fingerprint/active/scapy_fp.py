#!/usr/bin/env python3
"""
Scapy Fingerprint Collector — анализ TCP/ICMP стека для определения ОС.
Использует Scapy для отправки SYN и анализа TCP Options, TTL, Window Size.
"""

from __future__ import annotations

import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from scapy.all import IP, TCP, sr1, conf

from config import Fingerprint
from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set

# Отключаем вывод Scapy при ошибках, чтобы не засорять логи
conf.verb = 0


class ScapyFPCollector(ActiveCollector):
    PRIORITY = 35  # Очень высокий приоритет, базовый фингерпринтинг
    RELIABILITY = 95

    def __init__(self):
        super().__init__(timeout=1.0)
        self.workers = 32
        self.port = 80  # Целевой порт для SYN (можно сделать динамическим из context)

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        cached = cache_get(device.ip, "scapy_fp")
        if cached:
            return FingerprintResult(**cached, source="scapy_fp", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(
                source="scapy_fp",
                raw_data={"responded": False, "reason": "device_unavailable"},
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        fp_data = self._get_tcp_fingerprint(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if fp_data:
            result = FingerprintResult(
                source="scapy_fp",
                raw_data=fp_data,
                elapsed_ms=elapsed_ms,
                # Авто-генерация capabilities на основе ответов
                capabilities=["supports_scapy_fp"]
            )
        else:
            result = FingerprintResult(
                source="scapy_fp",
                raw_data={"responded": False, "reason": "no_response_or_filtered"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "scapy_fp", asdict(result))
        return result

    def _get_tcp_fingerprint(self, ip: str) -> dict | None:
        try:
            # Формируем IP + TCP SYN пакет
            # Динамически выбираем порт: если в будущем будем брать из context, то open_ports[0]
            # Пока используем 80 или 443 как наиболее вероятные открытые
            packet = IP(dst=ip) / TCP(dport=80, flags="S", window=29200)
            
            # Отправляем и ждем ответ
            response = sr1(packet, timeout=self.timeout, retry=0)
            
            if response is None:
                return None

            # Проверяем, что это TCP ответ (SA = SYN-ACK)
            if response.haslayer(TCP) and response[TCP].flags == "SA":
                tcp_opts = {}
                # Парсим TCP Options (кортежи вида ('MSS', 1460))
                for opt_name, opt_val in response[TCP].options:
                    if isinstance(opt_val, bytes):
                        tcp_opts[opt_name] = opt_val.hex()
                    else:
                        tcp_opts[opt_name] = opt_val

                return {
                    "responded": True,
                    "protocol": "TCP",
                    "ttl": response[IP].ttl,
                    "window_size": response[TCP].window,
                    "tcp_options": tcp_opts,
                    "ip_id": response[IP].id,
                    "df_flag": bool(response[IP].flags & 0x02),  # Don't Fragment
                }
            return None

        except Exception:
            return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        results: dict[str, FingerprintResult] = {}
        
        # Оптимизация: сканируем только те устройства, у которых есть открытые порты (из context TCP)
        targets = devices
        if context and "tcp" in context:
            tcp_ctx = context["tcp"]
            targets = [d for d in devices if tcp_ctx.get(d.ip) and tcp_ctx[d.ip].raw_data.get("responded")]

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    results[ip] = future.result()
                except Exception:
                    results[ip] = FingerprintResult(source="scapy_fp", elapsed_ms=0.0)
        return results
