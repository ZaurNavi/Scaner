#!/usr/bin/env python3
"""
Base Passive Collector + Aggregator.
ES-1.8.3: Полная миграция на List[Observation].
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

# ES-1.8.1: Normalization Layer Integration
from ..normalization import Normalizer, RuleRegistry
from ..normalization.models import (
    Observation as NormalizationObservation,
    ObservationMetadata,
    ObservationCategory,
)
from ..normalization.rules import dns, mdns

# Инициализация Normalization Layer при импорте
print("\n  [NORMALIZATION] Initializing Normalization Layer...")
print(f"  [NORMALIZATION] ✅ Rule Registry initialized ({RuleRegistry.count()} rules)")
for rule in RuleRegistry.get_all_rules():
    print(f"         • [{rule.priority}] {rule.id} - {rule.description} (protocol={rule.protocol})")


# ==============================================================================
# Observation — единица наблюдения от Passive Collector
# ==============================================================================

@dataclass
class Observation:
    """
    Единая единица наблюдения от Passive Collector.
    ES-1.8.3: Возвращается как List[Observation].
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
    ES-1.8.3: Единый контракт — observe() возвращает List[Observation].
    """
    
    descriptor: Any = None
    category: ObservationCategory = ObservationCategory.IDENTITY
    
    def __init__(self, configuration: ConfigurationManager):
        self.config = configuration
    
    @abstractmethod
    def observe(self, ips: List[str], context: Dict[str, Any] = None) -> List[Observation]:
        """
        ES-1.8.3: Возвращает List[Observation].
        """
        pass
    
    @property
    def id(self) -> str:
        return self.descriptor.id if self.descriptor else self.__class__.__name__.lower()
    
    @property
    def name(self) -> str:
        return self.descriptor.name if self.descriptor else self.__class__.__name__
    
    @property
    def version(self) -> str:
        return self.descriptor.version if self.descriptor else "0.0.0"
    
    @property
    def protocol(self) -> str:
        return self.descriptor.protocol if self.descriptor else "unknown"
    
    @property
    def capabilities(self) -> tuple:
        return self.descriptor.capabilities if self.descriptor else ()


# ==============================================================================
# CollectedData — агрегированные данные для устройства
# ==============================================================================

try:
    from .mdns import MDNSInfo
except ImportError:
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
    """
    hostname: str = ""
    mdns: MDNSInfo = field(default_factory=MDNSInfo)
    sources: Dict[str, FingerprintResult] = field(default_factory=dict)
    passive_observations: List[Observation] = field(default_factory=list)
    unified_observations: List[Any] = field(default_factory=list)


# ==============================================================================
# collect_all() — агрегатор
# ==============================================================================

def collect_all(
    ips: List[str],
    devices: List[Device],
    configuration: Optional[ConfigurationManager] = None
) -> Dict[str, CollectedData]:
    """
    ES-1.8.3: Работает с List[Observation] от всех коллекторов.
    """
    print(f"\n  [DEBUG] collect_all() запущен для {len(devices)} устройств")
    
    if configuration is None:
        configuration = get_config_manager()
    
    start_total = time.time()
    
    # ======================================================================
    # Passive Collectors через Factory
    # ======================================================================
    passive_results: Dict[str, List[Observation]] = {}
    passive_collectors: Dict[str, BasePassiveCollector] = {}
    passive_stats = []
    
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
        
        collector = PassiveCollectorFactory.create(descriptor, configuration)
        passive_collectors[collector_id] = collector
        
        start = time.time()
        try:
            # ES-1.8.3: observe() возвращает List[Observation]
            observations = collector.observe(ips, context={})
            passive_results[collector_id] = observations
            
            elapsed = (time.time() - start) * 1000
            count = len(observations)
            
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
    # Normalization Layer
    # ======================================================================
    print("\n  [NORMALIZATION] Normalizing observations...")
    
    normalizer = Normalizer(configuration)
    
    # ES-1.8.3: Собираем все Observation из всех коллекторов
    all_normalization_observations = []
    
    for collector_id, observations in passive_results.items():
        # ES-1.8.3: observations — это List[Observation]
        for obs in observations:
            # Конвертируем в NormalizationObservation
            # ES-1.8.3: Используем ObservationFactory для валидации
            from ..normalization import ObservationFactory
            
            # Определяем атрибут на основе данных
            if collector_id == "dns" and isinstance(obs.data, str):
                norm_obs = ObservationFactory.create_hostname(
                    collector_id=collector_id,
                    protocol=obs.protocol,
                    device_id=obs.metadata.get("ip", ""),
                    hostname=obs.data
                )
                all_normalization_observations.append(norm_obs)
            
            elif collector_id == "mdns":
                mdns_info = obs.data
                if hasattr(mdns_info, "hostname") and mdns_info.hostname:
                    norm_obs = ObservationFactory.create_hostname(
                        collector_id=collector_id,
                        protocol=obs.protocol,
                        device_id=obs.metadata.get("ip", ""),
                        hostname=mdns_info.hostname
                    )
                    all_normalization_observations.append(norm_obs)
                
                if hasattr(mdns_info, "model") and mdns_info.model:
                    norm_obs = ObservationFactory.create(
                        collector_id=collector_id,
                        protocol=obs.protocol,
                        device_id=obs.metadata.get("ip", ""),
                        attribute="model",
                        value=mdns_info.model
                    )
                    all_normalization_observations.append(norm_obs)
                
                if hasattr(mdns_info, "device_type") and mdns_info.device_type:
                    norm_obs = ObservationFactory.create(
                        collector_id=collector_id,
                        protocol=obs.protocol,
                        device_id=obs.metadata.get("ip", ""),
                        attribute="device_type",
                        value=mdns_info.device_type
                    )
                    all_normalization_observations.append(norm_obs)
                
                if hasattr(mdns_info, "services") and mdns_info.services:
                    norm_obs = ObservationFactory.create(
                        collector_id=collector_id,
                        protocol=obs.protocol,
                        device_id=obs.metadata.get("ip", ""),
                        attribute="services",
                        value=mdns_info.services
                    )
                    all_normalization_observations.append(norm_obs)
    
    # Строим category_map
    category_map = {}
    for collector_id, collector in passive_collectors.items():
        category_map[collector_id] = collector.category
    
    # Нормализуем через Batch API
    unified_observations = normalizer.normalize_many(
        all_normalization_observations,
        category_map
    )
    
    print(f"         • Normalized {len(unified_observations)} observations")
    
    # Группируем по IP
    unified_by_ip = {}
    for unified in unified_observations:
        device_id = unified.metadata.ip
        if device_id not in unified_by_ip:
            unified_by_ip[device_id] = []
        unified_by_ip[device_id].append(unified)
    
    # ======================================================================
    # Active Collectors (без изменений)
    # ======================================================================
    all_sources: Dict[str, Dict[str, FingerprintResult]] = {}
    context: Dict[str, Dict[str, FingerprintResult]] = {}
    collector_stats = []
    
    for collector in get_collectors(configuration):
        source = collector.source_name
        start = time.time()
        
        collector_results = {}
        for d in devices:
            cached = cache_get(d.ip, source)
            if cached:
                collector_results[d.ip] = FingerprintResult(**cached)
        
        uncached = [d for d in devices if d.ip not in collector_results]
        if uncached:
            results = collector.scan(uncached, context=context)
            collector_results.update(results)
        
        context[source] = collector_results
        
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
        if "dns" in passive_results:
            for obs in passive_results["dns"]:
                if obs.metadata.get("ip") == ip and isinstance(obs.data, str):
                    hostname = obs.data
                    break
        
        # Извлекаем MDNSInfo из mDNS observations
        mdns_info = MDNSInfo()
        if "mdns" in passive_results:
            for obs in passive_results["mdns"]:
                if obs.metadata.get("ip") == ip:
                    mdns_info = obs.data
                    break
        
        # ES-1.8.3: Добавляем unified observations
        ip_unified_observations = unified_by_ip.get(ip, [])
        
        result[ip] = CollectedData(
            hostname=hostname,
            mdns=mdns_info,
            sources=all_sources.get(ip, {}),
            passive_observations=passive_results.get("dns", []) + passive_results.get("mdns", []),
            unified_observations=ip_unified_observations
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
