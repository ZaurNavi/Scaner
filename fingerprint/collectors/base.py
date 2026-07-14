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
    
    # Статистика для таблицы (Requirement #10)
    collector_stats = []

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

        elapsed = (time.time() - start) * 1000
        collector_stats.append({
            "name": source,
            "elapsed": elapsed,
            "uncached": len(uncached),
            "status": "✅ OK" if elapsed < 5000 else "⚠️ Slow"
        })

    result = {}
    for d in devices:
        ip = d.ip
        result[ip] = CollectedData(
            hostname=hostnames.get(ip, ""),
            mdns=mdns_data.get(ip, MDNSInfo()),
            sources=all_sources.get(ip, {}),
        )
    
    total_time = (time.time() - start_total) * 1000
    
    # Вывод красивой таблицы статистики коллекторов
    print(f"\n  [STATS] Collector Performance:")
    print(f"  {'Collector':<15} | {'Elapsed':<10} | {'Uncached':<10} | {'Status'}")
    print(f"  " + "-" * 52)
    for stat in collector_stats:
        print(f"  {stat['name']:<15} | {stat['elapsed']:>7.1f} ms | {stat['uncached']:>8} | {stat['status']}")
    print(f"  " + "-" * 52)
    print(f"  [DEBUG] Итого: {total_time:.1f} мс\n")
    
    return result
