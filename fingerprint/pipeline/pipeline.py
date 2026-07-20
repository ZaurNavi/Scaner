#!/usr/bin/env python3
"""
FingerprintPipeline — внутренний координатор Fingerprint.
ES-1.8.2: Pipeline является внутренней реализацией FingerprintService.

Архитектурные принципы:
- Pipeline не является публичным API
- Pipeline вызывается только Service
- Pipeline stateless (не хранит состояние)
- Pipeline принимает FingerprintContext, возвращает UnifiedObservationBatch
- Zero Copy для UnifiedObservation
"""

from __future__ import annotations

import time
from typing import Dict, List

from configuration import ConfigurationManager

from ..active import get_collectors as get_active_collectors
from ..collectors.factory import PassiveCollectorFactory
from ..collectors.registry import PassiveRegistry
from ..collectors.base import Observation as PassiveObservation
from ..normalization import Normalizer
from ..normalization.models import (
    Observation as NormalizationObservation,
    ObservationMetadata,
    ObservationCategory,
)
from ..normalization.rules import dns, mdns  # Запускает регистрацию правил
from .batch import UnifiedObservationBatch, UnifiedObservationBatchBuilder
from .context import FingerprintContext
from .exceptions import PipelineExecutionError


class FingerprintPipeline:
    """
    Внутренний координатор Fingerprint.
    
    ES-1.8.2:
    - Не является публичным API
    - Вызывается только FingerprintService
    - Stateless (не хранит состояние)
    - Принимает FingerprintContext, возвращает UnifiedObservationBatch
    - Zero Copy для UnifiedObservation
    
    Pipeline выполняет полный цикл:
    1. Collector Stage (Active + Passive)
    2. Observation Stream
    3. Normalization Stage
    4. UnifiedObservationBuilder
    5. UnifiedObservationBatchBuilder
    6. UnifiedObservationBatch
    """
    
    def __init__(self, configuration: ConfigurationManager):
        """
        Dependency Injection через ConfigurationManager.
        
        Args:
            configuration: ConfigurationManager для всех зависимостей
        """
        self.config = configuration
        self.normalizer = Normalizer(configuration)
    
    def execute(self, context: FingerprintContext) -> UnifiedObservationBatch:
        """
        Выполняет полный цикл обработки.
        
        Args:
            context: FingerprintContext с входными данными
        
        Returns:
            UnifiedObservationBatch (immutable)
        
        Raises:
            PipelineExecutionError: Если Pipeline не может выполниться
        """
        start_time = time.time()
        
        try:
            # ==================================================================
            # Stage 1: Collector Stage
            # ==================================================================
            print("\n  [PIPELINE] Stage 1: Collecting observations...")
            
            # Passive Collectors через Registry
            passive_observations = self._collect_passive(context)
            
            # Active Collectors через Registry (legacy, но интегрированы)
            # В будущем Active тоже будет возвращать Observation
            active_results = self._collect_active(context)
            
            print(f"         • Passive: {len(passive_observations)} observations")
            print(f"         • Active: {len(active_results)} results (legacy)")
            
            # ==================================================================
            # Stage 2: Observation Stream
            # ==================================================================
            print("\n  [PIPELINE] Stage 2: Converting to Observation stream...")
            
            # Конвертируем Passive Observation в Normalization Observation
            normalization_observations = self._convert_to_normalization(
                passive_observations,
                context
            )
            
            print(f"         • Converted {len(normalization_observations)} observations")
            
            # ==================================================================
            # Stage 3: Normalization Stage
            # ==================================================================
            print("\n  [PIPELINE] Stage 3: Normalizing observations...")
            
            # Строим category_map из Passive Collectors
            category_map = self._build_category_map()
            
            # Нормализуем через Normalizer
            unified_observations = self.normalizer.normalize_many(
                normalization_observations,
                category_map
            )
            
            print(f"         • Normalized {len(unified_observations)} observations")
            
            # ==================================================================
            # Stage 4-5: UnifiedObservationBatchBuilder
            # ==================================================================
            print("\n  [PIPELINE] Stage 4-5: Building UnifiedObservationBatch...")
            
            builder = UnifiedObservationBatchBuilder()
            builder.extend(unified_observations)
            
            # ==================================================================
            # Stage 6: UnifiedObservationBatch
            # ==================================================================
            batch = builder.build(metadata={
                "scan_timestamp": context.scan_timestamp.isoformat(),
                "pipeline_version": "1.8.2",
                "elapsed_ms": (time.time() - start_time) * 1000
            })
            
            print(f"         • ✅ Built batch with {batch.count()} observations")
            
            return batch
            
        except Exception as e:
            raise PipelineExecutionError("execute", e)
    
    def _collect_passive(self, context: FingerprintContext) -> List[PassiveObservation]:
        """
        Запускает Passive Collectors через Registry.
        
        Pipeline не знает конкретных Collector.
        Он работает только через Registry.
        """
        all_observations = []
        
        # Получаем все включённые дескрипторы из Registry
        enabled_descriptors = list(PassiveRegistry.iter_enabled_descriptors(context.configuration))
        
        for descriptor in enabled_descriptors:
            # Создаём экземпляр через Factory
            collector = PassiveCollectorFactory.create(descriptor, context.configuration)
            
            # Запускаем коллектор
            observations_dict = collector.observe(list(context.ips), context={})
            
            # Преобразуем dict в list
            for ip, obs in observations_dict.items():
                all_observations.append(obs)
        
        return all_observations
    
    def _collect_active(self, context: FingerprintContext) -> Dict:
        """
        Запускает Active Collectors через Registry.
        
        ES-1.8.2: Active Collectors пока возвращают FingerprintResult (legacy).
        В будущем Active тоже будет возвращать Observation.
        """
        all_results = {}
        
        # Получаем все Active Collectors
        active_collectors = get_active_collectors(context.configuration)
        
        for collector in active_collectors:
            source = collector.source_name
            devices_list = list(context.devices)
            
            # Запускаем коллектор
            results = collector.scan(devices_list, context={})
            all_results[source] = results
        
        return all_results
    
    def _convert_to_normalization(
        self,
        passive_observations: List[PassiveObservation],
        context: FingerprintContext
    ) -> List[NormalizationObservation]:
        """
        Конвертирует Passive Observation в Normalization Observation.
        
        ES-1.8.2:
        - DNS: создаёт Observation с attribute="hostname"
        - mDNS: создаёт несколько Observations для каждого поля
        """
        all_normalization_observations = []
        
        for obs in passive_observations:
            timestamp = obs.timestamp
            
            # DNS: hostname
            if obs.collector_id == "dns":
                hostname = obs.data or ""
                if hostname:
                    norm_obs = NormalizationObservation(
                        observation_id=NormalizationObservation.generate_id(
                            collector_id=obs.collector_id,
                            device_id=obs.metadata.get("ip", ""),
                            attribute="hostname",
                            value=hostname
                        ),
                        collector_id=obs.collector_id,
                        protocol=obs.protocol,
                        device_id=obs.metadata.get("ip", ""),
                        attribute="hostname",
                        value=hostname,
                        timestamp=timestamp,
                        metadata=ObservationMetadata(ip=obs.metadata.get("ip", ""))
                    )
                    all_normalization_observations.append(norm_obs)
            
            # mDNS: hostname, model, device_type, services
            elif obs.collector_id == "mdns":
                mdns_info = obs.data
                ip = obs.metadata.get("ip", "")
                
                if hasattr(mdns_info, "hostname") and mdns_info.hostname:
                    norm_obs = NormalizationObservation(
                        observation_id=NormalizationObservation.generate_id(
                            collector_id=obs.collector_id,
                            device_id=ip,
                            attribute="hostname",
                            value=mdns_info.hostname
                        ),
                        collector_id=obs.collector_id,
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
                            collector_id=obs.collector_id,
                            device_id=ip,
                            attribute="model",
                            value=mdns_info.model
                        ),
                        collector_id=obs.collector_id,
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
                            collector_id=obs.collector_id,
                            device_id=ip,
                            attribute="device_type",
                            value=mdns_info.device_type
                        ),
                        collector_id=obs.collector_id,
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
                            collector_id=obs.collector_id,
                            device_id=ip,
                            attribute="services",
                            value=str(mdns_info.services)
                        ),
                        collector_id=obs.collector_id,
                        protocol=obs.protocol,
                        device_id=ip,
                        attribute="services",
                        value=mdns_info.services,
                        timestamp=timestamp,
                        metadata=ObservationMetadata(ip=ip)
                    )
                    all_normalization_observations.append(norm_obs)
        
        return all_normalization_observations
    
    def _build_category_map(self) -> Dict[str, ObservationCategory]:
        """
        Строит category_map из Passive Collectors.
        
        ES-1.8.2: Категория определяется Collector, не Normalizer.
        """
        category_map = {}
        
        for descriptor in PassiveRegistry.get_sorted_descriptors():
            # Создаём временный экземпляр для получения category
            # В будущем Collector должен предоставлять category через descriptor
            category_map[descriptor.id] = ObservationCategory.IDENTITY
        
        # Специальные маппинги
        category_map["dns"] = ObservationCategory.IDENTITY
        category_map["mdns"] = ObservationCategory.DISCOVERY
        
        return category_map
