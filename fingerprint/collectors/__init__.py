#!/usr/bin/env python3
"""
Fingerprint Collectors Module.
ES-1.8.0: Passive Framework с автоматической регистрацией.

Архитектура:
- Passive Framework: DNS, mDNS (и будущие LLMNR, NBNS, DHCP и т.д.)
- Active Framework: TCP, HTTP, SNMP, SSH, SMB, и т.д.

Автоматическая регистрация:
При импорте этого модуля все Passive Collectors автоматически
регистрируются в PassiveRegistry через декоратор @passive_collector.
"""

from configuration import get_config_manager

# ==============================================================================
# Passive Framework — импорт для автоматической регистрации
# ==============================================================================
from .registry import (
    PassiveRegistry,
    PassiveCollectorDescriptor,
    passive_collector
)

from .base import (
    BasePassiveCollector,
    Observation,
    CollectedData,
    collect_all
)

# Импорты коллекторов — это запускает декораторы @passive_collector
# и автоматически регистрирует их в PassiveRegistry
from .dns import DNSCollector, collect_hostnames
from .mdns import MDNSCollector, MDNSInfo, collect_mdns

# ==============================================================================
# Active Framework — импорт для обратной совместимости
# ==============================================================================
from ..active import FingerprintResult, get_collectors

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
    
    print("  [PASSIVE] Registered collectors:")
    for cid, descriptor in sorted(descriptors.items(), key=lambda x: x[1].priority):
        enabled_status = "enabled" if descriptor.enabled_by_default else "disabled"
        capabilities = ", ".join(descriptor.capabilities) if descriptor.capabilities else "none"
        print(f"         • {cid} (v{descriptor.version}) - {descriptor.name} - priority {descriptor.priority} - {enabled_status}")
        print(f"              Protocol: {descriptor.protocol} | Capabilities: {capabilities}")
    
    print(f"  [PASSIVE] ✅ Passive Framework initialized ({len(descriptors)} collectors)")


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
    "BasePassiveCollector",
    "Observation",
    "CollectedData",
    "collect_all",
    "DNSCollector",
    "collect_hostnames",
    "MDNSCollector",
    "MDNSInfo",
    "collect_mdns",
    # Active Framework
    "FingerprintResult",
    "get_collectors",
]
