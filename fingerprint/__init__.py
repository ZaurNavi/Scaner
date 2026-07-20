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

# ES-1.8.2: Новый публичный API
from .service import FingerprintService
from .pipeline import (
    FingerprintContext,
    UnifiedObservationBatch,
    UnifiedObservationBatchBuilder,
    BuilderAlreadyBuiltError,
)

# Обратная совместимость: legacy API для report.py и monitor.py
from .analysis import fingerprint_all

__all__ = [
    # ES-1.8.2: Новый API
    "FingerprintService",
    "FingerprintContext",
    "UnifiedObservationBatch",
    "UnifiedObservationBatchBuilder",
    "BuilderAlreadyBuiltError",
    # Legacy: обратная совместимость
    "fingerprint_all",
]
