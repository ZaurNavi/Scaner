#!/usr/bin/env python3
"""
Base Passive Collector + Aggregator.
ES-1.8.0: Единый контракт для всех Passive Collectors.
ES-1.8.1: Интеграция с Normalization Layer.

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
# ES-1.8.1: Normalization Layer Integration
# ==============================================================================
from ..normalization import Normalizer, RuleRegistry
from ..normalization.models import (
    Observation as NormalizationObservation,
    ObservationMetadata,
    ObservationCategory,
)
from ..normalization.rules import dns, mdns  # Запускает регистрацию правил

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
    
    # ES-1.8.1: Категория для нормализации
    category: ObservationCategory = ObservationCategory.IDENTITY
    
    def __init__(self, configuration: ConfigurationManager):
        """
        v1.8.0: Dependency Injection через ConfigurationManager.
        """
        self.config = configuration
    
    @abstractmethod
    def observe(self, ips: List[str], context: Dict[str, Any] = None) -> Dict[str, Observation]:
        """
        Наблюдает за сетью и возвращает наблюдения.
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
    
    v1.8.0: Добавлено поле passive_observations.
    v1.8.1: Добавлено поле unified_observations.
    """
    hostname: str = ""
    mdns: MDNSInfo = field(default_factory=MDNSInfo)
    sources: Dict[str, FingerprintResult] = field(default_factory=dict)
    passive_observations: Dict[str, Observation] = field(default_factory=dict)
    unified_observations: List[Any] = field(default_factory=list)  # ES-1.8.1


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
    
    v1.8.0: Использует PassiveCollectorFactory.
    v1.8.1: Добавлена нормализация через Normalizer.
    """
    print(f"\n  [DEBUG] collect_all() запущен для {len(devices)} устройств")
    
    if configuration is None:
        configuration = get_config_manager()
    
    start_total = time.time()
    
    # ======================================================================
    # v1.8.0: Passive Collectors через Factory
    # ======================================================================
    passive_results: Dict[str, Dict[str, Observation]] = {}
    passive_collectors: Dict[str, BasePassiveCollector] = {}  # ES-1.8.1
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
        passive_collectors[collector_id] = collector  # ES-1.8.1
        
        start = time.time()
        try:
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
    # ES-1.8.1: Normalization Layer
    # ======================================================================
    print("\n  [NORMALIZATION] Normalizing observations...")
    
    normalizer = Normalizer(configuration)
    
    # ES-1.8.1: Строим category_map из коллекторов
    category_map = {}
    for collector_id, collector in passive_collectors.items():
        category_map[collector_id] = collector.category
    
    # ES-1.8.1: Конвертируем Collector Observation → Normalization Observation
    # Для DNS: создаём Observation с attribute="hostname"
    # Для mDNS: создаём несколько Observations для каждого поля
    all_normalization_observations = []
    
    # ES-1.8.1: Счётчики для отладки DNS
    dns_total = 0
    dns_with_hostname = 0
    dns_empty_hostname = 0
    
    for collector_id, observations in passive_results.items():
        for ip, obs in observations.items():
            timestamp = obs.timestamp
            
            # DNS: hostname
            if collector_id == "dns":
                dns_total += 1
                hostname = obs.data or ""
                if hostname:
                    dns_with_hostname += 1
                    norm_obs = NormalizationObservation(
                        observation_id=NormalizationObservation.generate_id(
                            collector_id=collector_id,
                            device_id=ip,
                            attribute="hostname",
                            value=hostname
                        ),
                        collector_id=collector_id,
                        protocol=obs.protocol,
                        device_id=ip,
                        attribute="hostname",
                        value=hostname,
                        timestamp=timestamp,
                        metadata=ObservationMetadata(ip=ip)
                    )
                    all_normalization_observations.append(norm_obs)
                else:
                    dns_empty_hostname += 1
            
            # mDNS: hostname, model, device_type, services
            elif collector_id == "mdns":
                mdns_info = obs.data
                if hasattr(mdns_info, "hostname") and mdns_info.hostname:
                    norm_obs = NormalizationObservation(
                        observation_id=NormalizationObservation.generate_id(
                            collector_id=collector_id,
                            device_id=ip,
                            attribute="hostname",
                            value=mdns_info.hostname
                        ),
                        collector_id=collector_id,
                        protocol=obs.protocol,
                        device_id=ip,
                        attribute="hostname",
                        value=mdns_info.hostname,
                        timestamp=timestamp,
                        metadata=ObservationMetadata(ip=ip)
                    )
                    all_normalization_observations.append(norm_obs)
                
                if hasattr(mdns_info, "model") and mdns_info.model:
                    norm_obs = NormalizationObservation(
                        observation_id=NormalizationObservation.generate_id(
                            collector_id=collector_id,
                            device_id=ip,
                            attribute="model",
                            value=mdns_info.model
                        ),
                        collector_id=collector_id,
                        protocol=obs.protocol,
                        device_id=ip,
                        attribute="model",
                        value=mdns_info.model,
                        timestamp=timestamp,
                        metadata=ObservationMetadata(ip=ip)
                    )
                    all_normalization_observations.append(norm_obs)
                
                if hasattr(mdns_info, "device_type") and mdns_info.device_type:
                    norm_obs = NormalizationObservation(
                        observation_id=NormalizationObservation.generate_id(
                            collector_id=collector_id,
                            device_id=ip,
                            attribute="device_type",
                            value=mdns_info.device_type
                        ),
                        collector_id=collector_id,
                        protocol=obs.protocol,
                        device_id=ip,
                        attribute="device_type",
                        value=mdns_info.device_type,
                        timestamp=timestamp,
                        metadata=ObservationMetadata(ip=ip)
                    )
                    all_normalization_observations.append(norm_obs)
                
                if hasattr(mdns_info, "services") and mdns_info.services:
                    norm_obs = NormalizationObservation(
                        observation_id=NormalizationObservation.generate_id(
                            collector_id=collector_id,
                            device_id=ip,
                            attribute="services",
                            value=str(mdns_info.services)
                        ),
                        collector_id=collector_id,
                        protocol=obs.protocol,
                        device_id=ip,
                        attribute="services",
                        value=mdns_info.services,
                        timestamp=timestamp,
                        metadata=ObservationMetadata(ip=ip)
                    )
                    all_normalization_observations.append(norm_obs)
    
    # ES-1.8.1: Отладочный вывод DNS статистики
    if dns_total > 0:
        print(f"         • DNS stats: {dns_total} total, {dns_with_hostname} with hostname, {dns_empty_hostname} empty")
    
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
        
        hostname = ""
        if "dns" in passive_results and ip in passive_results["dns"]:
            hostname = passive_results["dns"][ip].data or ""
        
        mdns_info = MDNSInfo()
        if "mdns" in passive_results and ip in passive_results["mdns"]:
            mdns_info = passive_results["mdns"][ip].data
        
        ip_passive_observations = {}
        for collector_id, observations in passive_results.items():
            if ip in observations:
                ip_passive_observations[collector_id] = observations[ip]
        
        # ES-1.8.1: Добавляем unified observations
        ip_unified_observations = unified_by_ip.get(ip, [])
        
        result[ip] = CollectedData(
            hostname=hostname,
            mdns=mdns_info,
            sources=all_sources.get(ip, {}),
            passive_observations=ip_passive_observations,
            unified_observations=ip_unified_observations  # ES-1.8.1
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
