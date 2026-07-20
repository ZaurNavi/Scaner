#!/usr/bin/env python3
"""
FingerprintPipeline — внутренний координатор Fingerprint.
ES-1.8.2: Pipeline не знает о Active/Passive Framework.

Архитектурные принципы:
- Pipeline не знает о конкретных Framework
- Pipeline не делает конвертацию Observation
- Pipeline stateless
- Zero Copy для UnifiedObservation
"""

from __future__ import annotations

import time
from typing import List

from configuration import ConfigurationManager

from ..normalization import Normalizer
from ..normalization.models import Observation as NormalizationObservation
from ..normalization.models import ObservationMetadata
from .batch import UnifiedObservationBatch, UnifiedObservationBatchBuilder
from .context import FingerprintContext
from .exceptions import PipelineExecutionError
from .executor import CollectorExecutor, PassiveCollectorExecutor


class FingerprintPipeline:
    """
    Внутренний координатор Fingerprint.
    
    ES-1.8.2:
    - Не знает о Active/Passive Framework
    - Работает через CollectorExecutor
    - Не делает конвертацию Observation
    - Stateless
    - Zero Copy для UnifiedObservation
    
    Pipeline выполняет только координацию:
    1. Collector Stage (через Executor)
    2. Normalization Stage (через Normalizer)
    3. Batch Building (через Builder)
    """
    
    def __init__(
        self,
        configuration: ConfigurationManager,
        executor: CollectorExecutor = None
    ):
        """
        Dependency Injection через ConfigurationManager и Executor.
        
        Args:
            configuration: ConfigurationManager для всех зависимостей
            executor: CollectorExecutor (опционально, по умолчанию PassiveCollectorExecutor)
        """
        self.config = configuration
        self.normalizer = Normalizer(configuration)
        self.executor = executor or PassiveCollectorExecutor()
    
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
            # Stage 1: Collector Stage (через Executor)
            # ==================================================================
            print("\n  [PIPELINE] Stage 1: Collecting observations...")
            
            # Executor.run() → Observation[]
            # Pipeline не знает о конкретных коллекторах
            observations = self.executor.run(
                ips=list(context.ips),
                configuration=context.configuration
            )
            
            print(f"         • Collected {len(observations)} observations")
            
            # ==================================================================
            # Stage 2: Normalization Stage
            # ==================================================================
            print("\n  [PIPELINE] Stage 2: Normalizing observations...")
            
            # Конвертируем Observation → NormalizationObservation
            # Категория приходит из Descriptor, а не строится вручную
            normalization_observations = self._convert_observations(observations)
            
            # Нормализуем через Normalizer
            # Normalizer не строит category_map — категория из Descriptor
            unified_observations = self.normalizer.normalize_many(
                normalization_observations,
                category_map=None  # Категория уже в Observation
            )
            
            print(f"         • Normalized {len(unified_observations)} observations")
            
            # ==================================================================
            # Stage 3: Batch Building
            # ==================================================================
            print("\n  [PIPELINE] Stage 3: Building UnifiedObservationBatch...")
            
            builder = UnifiedObservationBatchBuilder()
            builder.extend(unified_observations)
            
            batch = builder.build(metadata={
                "scan_timestamp": context.scan_timestamp.isoformat(),
                "pipeline_version": "1.8.2",
                "elapsed_ms": (time.time() - start_time) * 1000
            })
            
            print(f"         • ✅ Built batch with {batch.count()} observations")
            
            return batch
            
        except Exception as e:
            raise PipelineExecutionError("execute", e)
    
    def _convert_observations(
        self,
        observations: List
    ) -> List[NormalizationObservation]:
        """
        Конвертирует Observation → NormalizationObservation.
        
        ES-1.8.2:
        - НЕ делает if dns / if mdns
        - Категория приходит из Observation (из Descriptor)
        - Pipeline не знает о конкретных протоколах
        """
        normalization_observations = []
        
        for obs in observations:
            # Категория из Descriptor (через collector.category)
            # Pipeline не строит category_map вручную
            category = obs.metadata.get("category")
            
            # Создаём NormalizationObservation
            # Pipeline не знает о hostname, model, services
            # Вся логика преобразования — в Normalization Rules
            norm_obs = NormalizationObservation(
                observation_id=NormalizationObservation.generate_id(
                    collector_id=obs.collector_id,
                    device_id=obs.metadata.get("ip", ""),
                    attribute="data",  # Атрибут определяется в Rules
                    value=obs.data
                ),
                collector_id=obs.collector_id,
                protocol=obs.protocol,
                device_id=obs.metadata.get("ip", ""),
                attribute="data",
                value=obs.data,
                timestamp=obs.timestamp,
                metadata=ObservationMetadata(
                    ip=obs.metadata.get("ip", ""),
                    extra=(("category", category),) if category else ()
                )
            )
            normalization_observations.append(norm_obs)
        
        return normalization_observations
