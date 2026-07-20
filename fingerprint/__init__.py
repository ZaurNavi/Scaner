#!/usr/bin/env python3
"""
Fingerprint — подсистема определения характеристик устройства.
ES-1.8.2: FingerprintService — единственный публичный API.

Архитектура:
- FingerprintService (публичный API)
- FingerprintPipeline (внутренний координатор)
- Active Framework (внутренний)
- Passive Framework (внутренний)
- Normalization Layer (внутренний)

Monitor работает исключительно с FingerprintService.
"""

from .service import FingerprintService
from .pipeline import (
    FingerprintContext,
    UnifiedObservationBatch,
    UnifiedObservationBatchBuilder,
    BuilderAlreadyBuiltError,
)

__all__ = [
    "FingerprintService",
    "FingerprintContext",
    "UnifiedObservationBatch",
    "UnifiedObservationBatchBuilder",
    "BuilderAlreadyBuiltError",
]
