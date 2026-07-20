#!/usr/bin/env python3
"""
FingerprintPipeline.
ES-1.8.3: Полностью protocol-agnostic. Просто передает List[Observation] в Normalizer.
"""

from __future__ import annotations

import time
from typing import List

from configuration import ConfigurationManager
from ..normalization import Normalizer
from ..normalization.models import Observation
from .batch import UnifiedObservationBatch, UnifiedObservationBatchBuilder
from .context import FingerprintContext
from .exceptions import PipelineExecutionError
from .executor import CollectorExecutor, PassiveCollectorExecutor


class FingerprintPipeline:
    def __init__(self, configuration: ConfigurationManager, executor: CollectorExecutor = None):
        self.config = configuration
        self.normalizer = Normalizer(configuration)
        self.executor = executor or PassiveCollectorExecutor()

    def execute(self, context: FingerprintContext) -> UnifiedObservationBatch:
        start_time = time.time()
        try:
            print("\n  [PIPELINE] Stage 1: Collecting observations...")
            # ES-1.8.3: Получаем чистый List[Observation]
            observations = self.executor.run(ips=list(context.ips), configuration=context.configuration)
            print(f"         • Collected {len(observations)} observations")

            print("\n  [PIPELINE] Stage 2: Normalizing observations...")
            # ES-1.8.3: Normalizer теперь принимает List[Observation] напрямую
            unified_observations = self.normalizer.normalize_many(observations)
            print(f"         • Normalized {len(unified_observations)} observations")

            print("\n  [PIPELINE] Stage 3: Building UnifiedObservationBatch...")
            builder = UnifiedObservationBatchBuilder()
            builder.extend(unified_observations)
            batch = builder.build(metadata={
                "scan_timestamp": context.scan_timestamp.isoformat(),
                "pipeline_version": "1.8.3",
                "elapsed_ms": (time.time() - start_time) * 1000
            })
            print(f"         • ✅ Built batch with {batch.count()} observations")
            return batch

        except Exception as e:
            raise PipelineExecutionError("execute", e)
