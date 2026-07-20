#!/usr/bin/env python3
"""
mDNS Normalization Rules.
ES-1.8.1: Правила возвращают NormalizationResult.
"""

from ..models import NormalizationResult, Observation, ObservationCategory
from ..registry import normalization_rule


@normalization_rule(
    id="mdns.hostname",
    category=ObservationCategory.IDENTITY,
    attribute="hostname",
    protocol="mDNS",
    priority=20,  # Ниже DNS
    description="Extract hostname from mDNS",
    version="1.0.0"
)
def normalize_mdns_hostname(obs: Observation) -> NormalizationResult:
    """Нормализует hostname из mDNS."""
    mdns_info = obs.value
    if hasattr(mdns_info, "hostname") and mdns_info.hostname:
        return NormalizationResult(
            value=mdns_info.hostname.strip().lower(),
            confidence=0.9,
            warnings=()
        )
    return NormalizationResult(
        value="",
        confidence=0.0,
        warnings=("no_hostname",)
    )


@normalization_rule(
    id="mdns.model",
    category=ObservationCategory.IDENTITY,
    attribute="model",
    protocol="mDNS",
    priority=10,
    description="Extract model from mDNS",
    version="1.0.0"
)
def normalize_mdns_model(obs: Observation) -> NormalizationResult:
    """Нормализует model из mDNS."""
    mdns_info = obs.value
    if hasattr(mdns_info, "model") and mdns_info.model:
        return NormalizationResult(
            value=mdns_info.model.strip(),
            confidence=0.9,
            warnings=()
        )
    return NormalizationResult(
        value="",
        confidence=0.0,
        warnings=("no_model",)
    )


@normalization_rule(
    id="mdns.device_type",
    category=ObservationCategory.IDENTITY,
    attribute="device_type",
    protocol="mDNS",
    priority=10,
    description="Extract device type from mDNS",
    version="1.0.0"
)
def normalize_mdns_device_type(obs: Observation) -> NormalizationResult:
    """Нормализует device_type из mDNS."""
    mdns_info = obs.value
    if hasattr(mdns_info, "device_type") and mdns_info.device_type:
        return NormalizationResult(
            value=mdns_info.device_type.strip(),
            confidence=0.8,
            warnings=()
        )
    return NormalizationResult(
        value="",
        confidence=0.0,
        warnings=("no_device_type",)
    )


@normalization_rule(
    id="mdns.services",
    category=ObservationCategory.SERVICE,
    attribute="services",
    protocol="mDNS",
    priority=10,
    description="Extract services list from mDNS",
    version="1.0.0"
)
def normalize_mdns_services(obs: Observation) -> NormalizationResult:
    """Нормализует список сервисов из mDNS."""
    mdns_info = obs.value
    if hasattr(mdns_info, "services") and mdns_info.services:
        return NormalizationResult(
            value=list(mdns_info.services),
            confidence=0.9,
            warnings=()
        )
    return NormalizationResult(
        value=[],
        confidence=0.0,
        warnings=("no_services",)
    )
