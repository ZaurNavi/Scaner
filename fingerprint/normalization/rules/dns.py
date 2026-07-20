#!/usr/bin/env python3
"""
DNS Normalization Rules.
ES-1.8.1: Правила возвращают NormalizationResult.
"""

from ..models import NormalizationResult, Observation, ObservationCategory
from ..registry import normalization_rule


@normalization_rule(
    id="dns.hostname",
    category=ObservationCategory.IDENTITY,
    attribute="hostname",
    protocol="DNS",
    priority=10,  # Высокий приоритет
    description="Extract hostname from DNS reverse lookup",
    version="1.0.0"
)
def normalize_dns_hostname(obs: Observation) -> NormalizationResult:
    """
    Нормализует hostname из DNS.
    
    ES-1.8.1: Возвращает NormalizationResult с confidence.
    """
    hostname = obs.value
    if not hostname:
        return NormalizationResult(
            value="",
            confidence=0.0,
            warnings=("empty_hostname",)
        )
    
    normalized = hostname.strip().lower()
    
    return NormalizationResult(
        value=normalized,
        confidence=1.0,
        warnings=()
    )
