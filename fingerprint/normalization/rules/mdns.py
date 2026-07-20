#!/usr/bin/env python3
"""
mDNS Normalization Rules.
ES-1.8.1: Правила для mDNS наблюдений.
"""

from ..models import Observation, ObservationCategory
from ..registry import normalization_rule


@normalization_rule(
    category=ObservationCategory.IDENTITY,
    attribute="hostname",
    priority=20,  # Ниже DNS
    description="Extract hostname from mDNS"
)
def normalize_mdns_hostname(obs: Observation) -> str:
    """
    Нормализует hostname из mDNS.
    
    Args:
        obs: Observation с MDNSInfo в value
    
    Returns:
        Нормализованный hostname
    """
    mdns_info = obs.value
    if hasattr(mdns_info, "hostname"):
        return mdns_info.hostname.strip().lower()
    return ""


@normalization_rule(
    category=ObservationCategory.IDENTITY,
    attribute="model",
    priority=10,
    description="Extract model from mDNS"
)
def normalize_mdns_model(obs: Observation) -> str:
    """
    Нормализует model из mDNS.
    
    Args:
        obs: Observation с MDNSInfo в value
    
    Returns:
        Model устройства
    """
    mdns_info = obs.value
    if hasattr(mdns_info, "model"):
        return mdns_info.model.strip()
    return ""


@normalization_rule(
    category=ObservationCategory.IDENTITY,
    attribute="device_type",
    priority=10,
    description="Extract device type from mDNS"
)
def normalize_mdns_device_type(obs: Observation) -> str:
    """
    Нормализует device_type из mDNS.
    
    Args:
        obs: Observation с MDNSInfo в value
    
    Returns:
        Тип устройства
    """
    mdns_info = obs.value
    if hasattr(mdns_info, "device_type"):
        return mdns_info.device_type.strip()
    return ""


@normalization_rule(
    category=ObservationCategory.SERVICE,
    attribute="services",
    priority=10,
    description="Extract services list from mDNS"
)
def normalize_mdns_services(obs: Observation) -> list:
    """
    Нормализует список сервисов из mDNS.
    
    Args:
        obs: Observation с MDNSInfo в value
    
    Returns:
        Список сервисов
    """
    mdns_info = obs.value
    if hasattr(mdns_info, "services"):
        return mdns_info.services
    return []
