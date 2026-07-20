#!/usr/bin/env python3
"""
DNS Normalization Rules.
ES-1.8.1: Правила для DNS наблюдений.
"""

from ..models import Observation, ObservationCategory
from ..registry import normalization_rule


@normalization_rule(
    category=ObservationCategory.IDENTITY,
    attribute="hostname",
    priority=10,  # Высокий приоритет
    description="Extract hostname from DNS reverse lookup"
)
def normalize_dns_hostname(obs: Observation) -> str:
    """
    Нормализует hostname из DNS.
    
    Args:
        obs: Observation с hostname в value
    
    Returns:
        Нормализованный hostname (строка)
    """
    hostname = obs.value
    if not hostname:
        return ""
    return hostname.strip().lower()
