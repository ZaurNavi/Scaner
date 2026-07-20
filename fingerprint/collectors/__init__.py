#!/usr/bin/env python3
"""
Fingerprint Collectors Module.
ES-1.8.3: Полная миграция на единый контракт Observation.
Удалены legacy: CollectedData, collect_all, Observation (из .base).

Архитектура:
- BasePassiveCollector: базовый класс для Passive Collectors
- Observation: импортируется из normalization.models (единый контракт)
- PassiveRegistry: реестр дескрипторов
- PassiveCollectorFactory: фабрика экземпляров
"""

from configuration import get_config_manager

# ==============================================================================
# Passive Framework — базовые компоненты
# ==============================================================================
from .registry import (
    PassiveRegistry,
    PassiveCollectorDescriptor,
    passive_collector
)

from .factory import PassiveCollectorFactory

from .base import BasePassiveCollector

# ES-1.8.3: Observation теперь импортируется из normalization.models
# (единый контракт для всех Collectors — Active и Passive)
from ..normalization.models import Observation

# Импорты коллекторов — это запускает декораторы @passive_collector
# и автоматически регистрирует их в PassiveRegistry
from .dns import DNSCollector
from .mdns import MDNSCollector

# ==============================================================================
# Инициализация Passive Framework
# ==============================================================================

def initialize_passive_framework():
    """
    Инициализирует Passive Framework и выводит информацию о зарегистрированных коллекторах.
    """
    print("\n  [PASSIVE] Initializing Passive Framework...")
    
    descriptors = PassiveRegistry.get_all_descriptors()
    
    if not descriptors:
        print("  [PASSIVE] ⚠️ No Passive Collectors registered")
        return
    
    print("  [PASSIVE] Registered collectors (sorted by priority):")
    for descriptor in PassiveRegistry.get_sorted_descriptors():
        enabled_status = "enabled" if descriptor.enabled_by_default else "disabled"
        capabilities = ", ".join(descriptor.capabilities) if descriptor.capabilities else "none"
        print(f"         • [{descriptor.priority}] {descriptor.id} (v{descriptor.version}) - {descriptor.name} - {enabled_status}")
        print(f"              Protocol: {descriptor.protocol} | Capabilities: {capabilities}")
    
    print(f"  [PASSIVE] ✅ Passive Framework initialized ({len(descriptors)} collectors)")
    print(f"  [PASSIVE] Factory: PassiveCollectorFactory ready")


# Автоматическая инициализация при импорте
initialize_passive_framework()

# ==============================================================================
# Экспорты
# ==============================================================================

__all__ = [
    # Passive Framework
    "PassiveRegistry",
    "PassiveCollectorDescriptor",
    "passive_collector",
    "PassiveCollectorFactory",
    "BasePassiveCollector",
    "Observation",  # ES-1.8.3: из normalization.models
    "DNSCollector",
    "MDNSCollector",
]
