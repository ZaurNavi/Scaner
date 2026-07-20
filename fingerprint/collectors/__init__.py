#!/usr/bin/env python3
"""
Fingerprint Collectors Module.
ES-1.8.0: Passive Framework с автоматической регистрацией через pkgutil.

Архитектура:
- Passive Framework: DNS, mDNS (и будущие LLMNR, NBNS, DHCP и т.д.)
- Active Framework: TCP, HTTP, SNMP, SSH, SMB, и т.д.

Auto Discovery:
При импорте этого модуля все Passive Collectors автоматически
обнаруживаются через pkgutil и регистрируются в PassiveRegistry.
"""

import pkgutil
import importlib

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

from .base import (
    BasePassiveCollector,
    Observation,
    CollectedData,
    collect_all
)

# ==============================================================================
# Active Framework — импорт для обратной совместимости
# ==============================================================================
from ..active import FingerprintResult, get_collectors

# ==============================================================================
# Auto Discovery — автоматическая регистрация Passive Collectors
# ==============================================================================

def _discover_passive_collectors():
    """
    Автоматически обнаруживает и импортирует все Passive Collectors.
    
    v1.8.0: Использует pkgutil для сканирования пакета.
    Каждый модуль, содержащий класс с декоратором @passive_collector,
    автоматически регистрируется в PassiveRegistry.
    
    Исключения:
    - base.py (базовый класс)
    - registry.py (реестр)
    - factory.py (фабрика)
    - __init__.py (текущий файл)
    """
    excluded_modules = {'base', 'registry', 'factory', '__init__'}
    
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        if module_name not in excluded_modules:
            try:
                # Импортируем модуль — это запускает декораторы @passive_collector
                importlib.import_module(f"{__name__}.{module_name}")
            except Exception as e:
                print(f"  [PASSIVE] ⚠️ Failed to import {module_name}: {e}")


# Автоматическое обнаружение коллекторов при импорте
_discover_passive_collectors()

# ==============================================================================
# Инициализация Passive Framework
# ==============================================================================

def initialize_passive_framework():
    """
    Инициализирует Passive Framework и выводит информацию о зарегистрированных коллекторах.
    
    ES-1.8.0: Информирующий вывод в консоли.
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
        print(f"              Class: {descriptor.collector_cls.__name__}")
    
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
    "Observation",
    "CollectedData",
    "collect_all",
    # Active Framework
    "FingerprintResult",
    "get_collectors",
]
