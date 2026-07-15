#!/usr/bin/env python3
"""
Декларативные правила оценки достоверности.
Никакой жёстко закодированной логики по конкретным брендам или моделям.
"""

from .categories import FactCategory


# Правила оценки: (категория, источник, вес)
CONFIDENCE_RULES = [
    # Vendor
    (FactCategory.VENDOR, "omada", 60),
    (FactCategory.VENDOR, "oui", 30),
    (FactCategory.VENDOR, "hostname", 15),
    (FactCategory.VENDOR, "http", 10),
    
    # Model
    (FactCategory.MODEL, "omada", 50),
    (FactCategory.MODEL, "mdns", 40),
    (FactCategory.MODEL, "hostname", 20),
    (FactCategory.MODEL, "ssdp", 15),
    
    # Hostname
    (FactCategory.HOSTNAME, "omada", 50),
    (FactCategory.HOSTNAME, "mdns", 40),
    (FactCategory.HOSTNAME, "dhcp", 30),
    (FactCategory.HOSTNAME, "dns", 20),
    
    # OS
    (FactCategory.OS, "omada", 60),
    (FactCategory.OS, "http", 40),
    (FactCategory.OS, "ttl", 30),
    (FactCategory.OS, "tcp", 20),
    
    # Device Type
    (FactCategory.DEVICE_TYPE, "omada", 50),
    (FactCategory.DEVICE_TYPE, "mdns", 40),
    (FactCategory.DEVICE_TYPE, "ssdp", 30),
    (FactCategory.DEVICE_TYPE, "http", 20),
    
    # SSID
    (FactCategory.SSID, "omada", 70),
    
    # Access Point
    (FactCategory.ACCESS_POINT, "omada", 70),
    
    # VLAN
    (FactCategory.VLAN, "omada", 70),
    
    # Radio
    (FactCategory.RADIO, "omada", 70),
    
    # WiFi Capability
    (FactCategory.WIFI_CAPABILITY, "omada", 70),
]


def get_rules_for_category(category: FactCategory) -> list:
    """Возвращает все правила для указанной категории."""
    return [(source, weight) for cat, source, weight in CONFIDENCE_RULES if cat == category]


def get_weight(category: FactCategory, source: str) -> int:
    """Возвращает вес для конкретной категории и источника."""
    for cat, src, weight in CONFIDENCE_RULES:
        if cat == category and src == source:
            return weight
    return 0
