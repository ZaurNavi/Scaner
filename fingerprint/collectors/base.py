#!/usr/bin/env python3
"""
Base Passive Collector + Aggregator.
ES-1.8.0: Единый контракт для всех Passive Collectors.

Архитектура:
- BasePassiveCollector: абстрактный базовый класс
- Observation: единица наблюдения
- CollectedData: агрегированные данные для устройства
- collect_all(): агрегатор, запускающий все коллекторы через Factory
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from models import Device
from configuration import ConfigurationManager, get_config_manager

from .registry import PassiveRegistry
from .factory import PassiveCollectorFactory
from ..active import FingerprintResult, get_collectors
from storage.active_cache import get as cache_get, set as cache_set


# ==============================================================================
# Observation — единица наблюдения от Passive Collector
# ==============================================================================

@dataclass
class Observation:
    """
    Единая единица наблюдения от Passive Collector.
    
    Zero Knowledge Principle:
    - Не знает о Platform Core
    - Не знает о Knowledge Layer
    - Не знает о Event Engine
    - Только данные наблюдения
    """
    collector_id: str
    protocol: str
    timestamp: datetime
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


# ==============================================================================
# BasePassiveCollector — абстрактный базовый класс
# ==============================================================================

class BasePassiveCollector(ABC):
    """
    Абстрактный базовый класс для всех Passive Collectors.
    
    Единый контракт:
    - observe(ips, context) -> dict[str, Observation]
    
    Zero Knowledge Principle:
    - Коллектор не знает, кто его вызывает
    - Коллектор не знает, кто использует результат
    - Коллектор выполняет только одну задачу:
      получить входные данные → сформировать Observation → вернуть
    """
    
    # Дескриптор устанавливается декоратором @passive_collector
    descriptor: Any = None
    
    def __init__(self, configuration: ConfigurationManager):
        """
        v1.8.0: Dependency Injection через ConfigurationManager.
        
        Args:
            configuration: ConfigurationManager для получения настроек
        """
        self.config = configuration
    
    @abstractmethod
    def observe(self, ips: List[str], context: Dict[str, Any] = None) -> Dict[str, Observation]:
        """
        Наблюдает за сетью и возвращает наблюдения.
        
        Args:
            ips: Список IP-адресов для наблюдения
            context: Контекст от предыдущих стадий (опционально)
        
        Returns:
            Dict[ip, Observation] — наблюдения для каждого IP
        """
        pass
    
    @property
    def id(self) -> str:
        """ID коллектора."""
        return self.descriptor.id if self.descriptor else self.__class__.__name__.lower()
    
    @property
    def name(self) -> str:
        """Имя коллектора."""
        return self.descriptor.name if self.descriptor else self.__class__.__name__
    
    @property
    def version(self) -> str:
        """Версия коллектора."""
        return self.descriptor.version if self.descriptor else "0.0.0"
    
    @property
    def protocol(self) -> str:
        """Протокол коллектора."""
        return self.descriptor.protocol if self.descriptor else "unknown"
    
    @property
    def capabilities(self) -> tuple:
        """Возможности коллектора."""
        return self.descriptor.capabilities if self.descriptor else ()


# ==============================================================================
# CollectedData — агрегированные данные для устройства
# ==============================================================================

# Импортируем MDNSInfo из mdns.py для обратной совместимости
try:
    from .mdns import MDNSInfo
except ImportError:
    # Fallback для случая, когда mdns ещё не импортирован
    @dataclass
    class MDNSInfo:
        hostname: str = ""
        model: str = ""
        device_type: str = ""
        services: list = field(default_factory=list)


@dataclass
class CollectedData:
    """
    Агрегированные данные для устройства.
    
    v1.8.0: Добавлено поле passive_observations для хранения
    результатов всех Passive Collectors.
    """
    hostname: str = ""
    mdns: MDNSInfo = field(default_factory=MDNSInfo)
    sources: Dict[str, FingerprintResult] = field(default_factory=dict)
    passive_observations: Dict[str, Observation] = field(default_factory=dict)


# ==============================================================================
# collect_all() — агрегатор
# ==============================================================================

def collect_all(
    ips: List[str],
    devices: List[Device],
    configuration: Optional[ConfigurationManager] = None
) -> Dict[str, CollectedData]:
    """
    Агрегирует данные от всех Passive и Active коллекторов.
    
    v1.8.0: Использует PassiveCollectorFactory для создания экземпляров.
    
    Args:
        ips: Список IP-адресов
        devices: Список устройств
        configuration: ConfigurationManager (опционально)
    
    Returns:
        Dict[ip, CollectedData] — агрегированные данные для каждого IP
    """
    print(f"\n  [DEBUG] collect_all() запущен для {len(devices)} устройств")
    
    # v1.8.0: Получаем конфигурацию, если она не передана явно
    if configuration is None:
        configuration = get_config_manager()
    
    start_total = time.time()
    
    # ======================================================================
    # v1.8.0: Passive Collectors через Factory
    # ======================================================================
    passive_results: Dict[str, Dict[str, Observation]] = {}
    passive_stats = []
    
    # Получаем все включённые дескрипторы из Registry
    enabled_descriptors = list(PassiveRegistry.iter_enabled_descriptors(configuration))
    
    print(f"\n  [PASSIVE] Running {len(enabled_descriptors)} Passive Collector(s)...")
    
    for descriptor in enabled_descriptors:
        collector_id = descriptor.id
        collector_name = descriptor.name
        collector_version = descriptor.version
        collector_priority = descriptor.priority
        
        print(f"\n  [PASSIVE] [{collector_priority}] {collector_name} (v{collector_version})")
        print(f"         • Protocol: {descriptor.protocol}")
        print(f"         • Capabilities: {', '.join(descriptor.capabilities) if descriptor.capabilities else 'none'}")
        
        # v1.8.0: Создаём экземпляр через Factory
        collector = PassiveCollectorFactory.create(descriptor, configuration)
        
        start = time.time()
        try:
            # Запускаем коллектор
            observations = collector.observe(ips, context={})
            passive_results[collector_id] = observations
            
            elapsed = (time.time() - start) * 1000
            count = len(observations)
            
            # Информируем о результате
            print(f"         • ✅ Collected {count} observations in {elapsed:.1f} ms")
            
            passive_stats.append({
                "name": collector_name,
                "id": collector_id,
                "priority": collector_priority,
                "elapsed": elapsed,
                "count": count,
                "status": "✅ OK" if elapsed < 5000 else "⚠️ Slow"
            })
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"         • ❌ Failed: {e}")
            passive_stats.append({
                "name": collector_name,
                "id": collector_id,
                "priority": collector_priority,
                "elapsed": elapsed,
                "count": 0,
                "status": f"❌ Error: {e}"
            })
    
    # ======================================================================
    # Active Collectors (без изменений)
    # ======================================================================
    all_sources: Dict[str, Dict[str, FingerprintResult]] = {}
    context: Dict[str, Dict[str, FingerprintResult]] = {}
    collector_stats = []
    
    for collector in get_collectors(configuration):
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
    
    # ======================================================================
    # Сборка результатов
    # ======================================================================
    result = {}
    for d in devices:
        ip = d.ip
        
        # Извлекаем hostname из DNS observations
        hostname = ""
        if "dns" in passive_results and ip in passive_results["dns"]:
            hostname = passive_results["dns"][ip].data or ""
        
        # Извлекаем MDNSInfo из mDNS observations
        mdns_info = MDNSInfo()
        if "mdns" in passive_results and ip in passive_results["mdns"]:
            mdns_info = passive_results["mdns"][ip].data
        
        # Собираем все passive observations для этого IP
        ip_passive_observations = {}
        for collector_id, observations in passive_results.items():
            if ip in observations:
                ip_passive_observations[collector_id] = observations[ip]
        
        result[ip] = CollectedData(
            hostname=hostname,
            mdns=mdns_info,
            sources=all_sources.get(ip, {}),
            passive_observations=ip_passive_observations
        )
    
    total_time = (time.time() - start_total) * 1000
    
    # ======================================================================
    # Вывод статистики
    # ======================================================================
    print(f"\n  [STATS] Passive Collectors Performance:")
    print(f"  {'Priority':<8} | {'Collector':<20} | {'ID':<10} | {'Elapsed':<10} | {'Count':<8} | {'Status'}")
    print(f"  " + "-" * 82)
    for stat in sorted(passive_stats, key=lambda x: x["priority"]):
        print(f"  {stat['priority']:<8} | {stat['name']:<20} | {stat['id']:<10} | {stat['elapsed']:>7.1f} ms | {stat['count']:>6} | {stat['status']}")
    print(f"  " + "-" * 82)
    
    print(f"\n  [STATS] Active Collectors Performance:")
    print(f"  {'Collector':<15} | {'Elapsed':<10} | {'Uncached':<10} | {'Status'}")
    print(f"  " + "-" * 52)
    for stat in collector_stats:
        print(f"  {stat['name']:<15} | {stat['elapsed']:>7.1f} ms | {stat['uncached']:>8} | {stat['status']}")
    print(f"  " + "-" * 52)
    print(f"  [DEBUG] Итого: {total_time:.1f} мс\n")
    
    return result
