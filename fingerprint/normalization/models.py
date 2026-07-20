#!/usr/bin/env python3
"""
Models — Observation, UnifiedObservation, NormalizationResult.
ES-1.8.3: Добавлен contract_version, строгая типизация.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Tuple, Union

# ==============================================================================
# ObservationCategory
# ==============================================================================
class ObservationCategory(Enum):
    IDENTITY = "identity"
    NETWORK = "network"
    SERVICE = "service"
    TRANSPORT = "transport"
    SECURITY = "security"
    APPLICATION = "application"
    TIMING = "timing"
    VENDOR = "vendor"
    DISCOVERY = "discovery"
    CONNECTIVITY = "connectivity"
    FINGERPRINT = "fingerprint"
    TOPOLOGY = "topology"

# ==============================================================================
# NormalizedValue
# ==============================================================================
NormalizedValue = Union[str, int, float, bool, List[Any], Dict[str, Any]]

# ==============================================================================
# ObservationMetadata (Strictly Typed)
# ==============================================================================
@dataclass(frozen=True)
class ObservationMetadata:
    ip: str = ""
    mac: str = ""
    hostname: str = ""
    protocol_version: str = ""
    source_port: int = 0
    destination_port: int = 0
    extra: Tuple[Tuple[str, str], ...] = ()

    def get_extra(self, key: str, default: str = "") -> str:
        for k, v in self.extra:
            if k == key: return v
        return default

# ==============================================================================
# Observation (ES-1.8.3: Added contract_version)
# ==============================================================================
@dataclass(frozen=True)
class Observation:
    contract_version: int = 1  # ES-1.8.3: Domain Contract Version
    observation_id: str = ""
    collector_id: str = ""
    protocol: str = ""
    device_id: str = ""
    attribute: str = ""
    value: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: ObservationMetadata = field(default_factory=ObservationMetadata)

    @staticmethod
    def generate_id(collector_id: str, device_id: str, attribute: str, value: Any) -> str:
        content = f"{collector_id}:{device_id}:{attribute}:{value}"
        return hashlib.sha256(content.encode()).hexdigest()

# ==============================================================================
# NormalizationResult & UnifiedObservation
# ==============================================================================
@dataclass(frozen=True)
class NormalizationResult:
    value: NormalizedValue
    confidence: float = 1.0
    warnings: Tuple[str, ...] = ()
    metadata: Tuple[Tuple[str, str], ...] = ()

@dataclass(frozen=True)
class UnifiedObservation:
    observation_id: str
    collector_id: str
    protocol: str
    category: ObservationCategory
    attribute: str
    normalized_value: NormalizedValue
    confidence: float
    timestamp: datetime
    warnings: Tuple[str, ...] = ()
    metadata: ObservationMetadata = field(default_factory=ObservationMetadata)

    def is_immutable(self) -> bool: return True
