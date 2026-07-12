#!/usr/bin/env python3
"""
TTL Collector — сбор данных о времени жизни пакетов.

Архитектура:
- Только собирает сырые данные (ttl, latency, alive)
- НЕ определяет ОС — это делает Correlation Engine
"""

from __future__ import annotations

import time
from dataclasses import asdict

from config import Fingerprint
from models import Device

from .base import ActiveCollector, FingerprintResult
from .ping import ping
from storage.active_cache import get as cache_get, set as cache_set


class TTLCollector(ActiveCollector):
    """
    Собирает TTL через ping.
    НЕ интерпретирует данные — только собирает факты.
    """

    PRIORITY = 40
    RELIABILITY = 20

    def __init__(self):
        super().__init__(timeout=Fingerprint.TTL_TIMEOUT)
        self.count = Fingerprint.TTL_COUNT

    def collect(self, device: Device) -> FingerprintResult:
        """
        Отправляет ping и собирает сырые данные.
        НЕ определяет ОС — это делает Correlation Engine.
        """
        start_time = time.time()

        # Проверка кэша
        cached = cache_get(device.ip, "ttl")
        if cached:
            return FingerprintResult(**cached, source="ttl", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(
                source="ttl",
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        ping_result = ping(device.ip, timeout=self.timeout, count=self.count)

        raw_data = {
            "alive": ping_result.alive,
            "ttl": ping_result.ttl,
            "latency_ms": ping_result.latency_ms,
            "exit_code": ping_result.exit_code,
            "command": ping_result.command,
        }

        elapsed_ms = (time.time() - start_time) * 1000

        # Возвращаем ТОЛЬКО сырые данные — без os, confidence, reason
        result = FingerprintResult(
            source="ttl",
            ttl=ping_result.ttl,
            latency_ms=ping_result.latency_ms,
            raw_data=raw_data,
            elapsed_ms=elapsed_ms,
        )

        # Сохранение в кэш
        cache_set(device.ip, "ttl", asdict(result))

        return result
