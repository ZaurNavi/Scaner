#!/usr/bin/env python3
"""
Агрегация коллекторов с поддержкой зависимостей и кэша.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from models import Device

from .dns import collect_hostnames
from .mdns import collect_mdns, MDNSInfo
from ..active import FingerprintResult, get_collectors
from storage.active_cache import get as cache_get, set as cache_set


@dataclass
class CollectedData:
    hostname: str = ""
    mdns: MDNSInfo = field(default_factory=MDNSInfo)
    sources: dict[str, FingerprintResult] = field(default_factory=dict)


def collect_all(ips: list[str], devices: list[Device]) -> dict[str, CollectedData]:
    print(f"\n  [DEBUG] collect_all() запущен для {len(devices)} устройств")
    
    start_total = time.time()
    
    # DNS
    start = time.time()
    hostnames = collect_hostnames(ips)
    print(f"  [DEBUG] DNS: {(time.time() - start) * 1000:.1f} мс")
    
    # mDNS
    start = time.time()
    mdns_data = collect_mdns(ips)
    print(f"  [DEBUG] mDNS: {(time.time() - start) * 1000:.1f} мс")

    all_sources: dict[str, dict[str, FingerprintResult]] = {}
    context: dict[str, dict[str, FingerprintResult]] = {}

    for collector in get_collectors():
        source = collector.source_name
        start = time.time()

        # Проверка кэша для каждого устройства
        collector_results = {}
        for d in devices:
            cached = cache_get(d.ip, source)
            if cached:
                collector_results[d.ip] = FingerprintResult(**cached)

        # Запуск коллектора только для устройств без кэша
        uncached = [d for d in devices if d.ip not in collector_results]
        if uncached:
            results = collector.scan(uncached, context=context)
            collector_results.update(results)

        # Сохранение в контекст для зависимых коллекторов
        context[source] = collector_results

        # Сборка all_sources
        for ip, res in collector_results.items():
            if ip not in all_sources:
                all_sources[ip] = {}
            all_sources[ip][source] = res

        print(f"  [DEBUG] {source}: {(time.time() - start) * 1000:.1f} мс ({len(uncached)} uncached)")

    result = {}
    for d in devices:
        ip = d.ip
        result[ip] = CollectedData(
            hostname=hostnames.get(ip, ""),
            mdns=mdns_data.get(ip, MDNSInfo()),
            sources=all_sources.get(ip, {}),
        )
    
    print(f"  [DEBUG] Итого: {(time.time() - start_total) * 1000:.1f} мс\n")
    
    return result
