#!/usr/bin/env python3
"""
TTL Normalization Rules.
ES-1.8.1: Правила возвращают NormalizationResult.
"""

from ..models import NormalizationResult, Observation, ObservationCategory
from ..registry import normalization_rule


@normalization_rule(
    id="identity.ttl",
    category=ObservationCategory.IDENTITY,
    attribute="ttl",
    protocol="TTL",
    priority=10,
    description="Normalize TTL value to integer",
    version="1.0.0"
)
def normalize_ttl(obs: Observation) -> NormalizationResult:
    """
    Нормализует TTL значение.
    
    ES-1.8.1: Приводит к int, возвращает NormalizationResult.
    """
    ttl_value = obs.value
    
    # Пытаемся преобразовать в int
    try:
        ttl_int = int(ttl_value)
        
        # TTL должен быть в диапазоне 0-255
        if not (0 <= ttl_int <= 255):
            return NormalizationResult(
                value=None,
                confidence=0.0,
                warnings=("ttl_out_of_range",)
            )
        
        return NormalizationResult(
            value=ttl_int,
            confidence=1.0,
            warnings=()
        )
    except (ValueError, TypeError):
        return NormalizationResult(
            value=None,
            confidence=0.0,
            warnings=("invalid_ttl_value",)
        )
