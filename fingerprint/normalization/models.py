#!/usr/bin/env python3
"""
Models — Observation, UnifiedObservation, NormalizationResult.
ES-1.8.1: Чистая архитектура без transport, с типизированными значениями.

Архитекторские принципы:
- Observation не знает transport (только protocol)
- Normalizer не угадывает категорию (из RuleDescriptor)
- Все значения типизированы (NormalizedValue)
- Metadata строго типизирована (ObservationMetadata)
- observation_id стабильный (без timestamp)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Tuple, Union


# ==============================================================================
# ObservationCategory — расширенный Enum (пункт 9)
# ==============================================================================

class ObservationCategory(Enum):
    """
    Категории наблюдений.
    
    ES-1.8.1: Строки запрещены, только Enum.
    Расширен для будущих протоколов (LLMNR, NBNS, DHCP, JA3 и т.д.).
    """
    IDENTITY = "identity"           # hostname, model, device_type, vendor
    NETWORK = "network"             # IP, MAC, VLAN, subnet
    SERVICE = "service"             # HTTP, SSH, SMB, SSDP
    TRANSPORT = "transport"         # TCP, UDP, TLS
    SECURITY = "security"           # TLS, JA3, certificates
    APPLICATION = "application"     # HTTP headers, user-agent
    TIMING = "timing"               # uptime, latency, TTL
    VENDOR = "vendor"               # OUI, manufacturer
    DISCOVERY = "discovery"         # mDNS, SSDP, WSD
    CONNECTIVITY = "connectivity"   # ping, traceroute, hops
    FINGERPRINT = "fingerprint"     # TCP options, window size
    TOPOLOGY = "topology"           # switch port, LLDP/CDP


# ==============================================================================
# NormalizedValue — типизированные значения (пункт 3)
# ==============================================================================

# ES-1.8.1: Строгая типизация вместо Any
NormalizedValue = Union[str, int, float, bool, List[Any], Dict[str, Any]]


# ==============================================================================
# ObservationMetadata — строго типизированная metadata (пункт 5)
# ==============================================================================

@dataclass(frozen=True)
class ObservationMetadata:
    """
    Строго типизированные метаданные Observation.
    
    ES-1.8.1: Никакого Dict[str, Any] — только фиксированные поля.
    """
    ip: str = ""
    mac: str = ""
    hostname: str = ""
    protocol_version: str = ""
    source_port: int = 0
    destination_port: int = 0
    extra: Tuple[Tuple[str, str], ...] = ()  # Immutable tuple of (key, value)
    
    def get_extra(self, key: str, default: str = "") -> str:
        """Получает значение из extra по ключу."""
        for k, v in self.extra:
            if k == key:
                return v
        return default


# ==============================================================================
# Observation — сырая запись (пункт 1, 4, 5)
# ==============================================================================

@dataclass(frozen=True)
class Observation:
    """
    Сырая запись наблюдения от Collector.
    
    ES-1.8.1:
    - БЕЗ transport (только protocol)
    - observation_id стабильный (без timestamp)
    - metadata строго типизирована
    """
    observation_id: str
    collector_id: str
    protocol: str
    device_id: str  # IP или MAC
    attribute: str
    value: Any
    timestamp: datetime
    metadata: ObservationMetadata = field(default_factory=ObservationMetadata)
    
    @staticmethod
    def generate_id(
        collector_id: str,
        device_id: str,
        attribute: str,
        value: Any
    ) -> str:
        """
        Генерирует стабильный observation_id через SHA256.
        
        ES-1.8.1 (пункт 4): БЕЗ timestamp.
        Один и тот же факт = один и тот же ID.
        """
        content = f"{collector_id}:{device_id}:{attribute}:{value}"
        return hashlib.sha256(content.encode()).hexdigest()


# ==============================================================================
# NormalizationResult — результат нормализации (пункт 8)
# ==============================================================================

@dataclass(frozen=True)
class NormalizationResult:
    """
    Результат нормализации от Rule handler.
    
    ES-1.8.1 (пункт 8): Правило возвращает не просто value,
    а полноценный результат с confidence, warnings, metadata.
    """
    value: NormalizedValue
    confidence: float = 1.0
    warnings: Tuple[str, ...] = ()
    metadata: Tuple[Tuple[str, str], ...] = ()


# ==============================================================================
# UnifiedObservation — нормализованное наблюдение (пункт 3)
# ==============================================================================

@dataclass(frozen=True)
class UnifiedObservation:
    """
    Нормализованное наблюдение.
    
    ES-1.8.1:
    - Immutable (frozen=True)
    - normalized_value типизирован (NormalizedValue)
    - category из RuleDescriptor (не угадывается)
    - Независимость: не содержит Profile, Session, Knowledge и т.д.
    """
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
    
    def is_immutable(self) -> bool:
        """UnifiedObservation действительно immutable."""
        return True
