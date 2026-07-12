#!/usr/bin/env python3
"""
Правила корреляции — определяют тип устройства по комбинации признаков.
"""

from __future__ import annotations
from dataclasses import dataclass
from .capabilities import DeviceCapabilities


@dataclass
class CorrelationRule:
    """
    Правило корреляции.
    """
    name: str
    condition: callable  # (device, capabilities, collected) -> bool
    result: dict  # {os, model, device_type, confidence, reason}
    priority: int = 50  # чем выше, тем важнее


# Базовые правила
RULES: list[CorrelationRule] = [
    
    # MikroTik RouterOS
    CorrelationRule(
        name="MikroTik RouterOS",
        condition=lambda d, c, col: (
            c.router and 
            (8291 in col.sources.get("tcp", {}).ports or 
             8728 in col.sources.get("tcp", {}).ports)
        ),
        result={
            "os": "RouterOS",
            "model": "",
            "device_type": "Router",
            "vendor": "MikroTik",
            "confidence": 90,
            "reason": "MikroTik ports detected (8291/8728)"
        },
        priority=90
    ),
    
    # IP Camera
    CorrelationRule(
        name="IP Camera",
        condition=lambda d, c, col: (
            c.camera and 
            (554 in col.sources.get("tcp", {}).ports or 
             8000 in col.sources.get("tcp", {}).ports)
        ),
        result={
            "os": "Embedded Linux",
            "model": "",
            "device_type": "IP Camera",
            "vendor": "",
            "confidence": 85,
            "reason": "RTSP/HTTP ports detected (554/8000)"
        },
        priority=85
    ),
    
    # Printer
    CorrelationRule(
        name="Network Printer",
        condition=lambda d, c, col: (
            c.printer and 
            (9100 in col.sources.get("tcp", {}).ports or 
             631 in col.sources.get("tcp", {}).ports)
        ),
        result={
            "os": "Embedded",
            "model": "",
            "device_type": "Printer",
            "vendor": "",
            "confidence": 85,
            "reason": "Printer ports detected (9100/631)"
        },
        priority=85
    ),
    
    # Android phone (silent)
    CorrelationRule(
        name="Android Phone (Silent)",
        condition=lambda d, c, col: (
            not c.icmp and 
            not c.tcp and 
            d.vendor and 
            "xiaomi" in d.vendor.lower()
        ),
        result={
            "os": "Android",
            "model": "",
            "device_type": "Smartphone",
            "vendor": d.vendor,
            "confidence": 70,
            "reason": "Xiaomi vendor + no ICMP/TCP (firewall)"
        },
        priority=70
    ),
    
    # iOS device (silent)
    CorrelationRule(
        name="iOS Device (Silent)",
        condition=lambda d, c, col: (
            not c.icmp and 
            not c.tcp and 
            d.vendor and 
            "apple" in d.vendor.lower()
        ),
        result={
            "os": "iOS",
            "model": "",
            "device_type": "Smartphone",
            "vendor": d.vendor,
            "confidence": 70,
            "reason": "Apple vendor + no ICMP/TCP (firewall)"
        },
        priority=70
    ),
    
    # Linux device (TTL only)
    CorrelationRule(
        name="Linux Device",
        condition=lambda d, c, col: (
            c.icmp and 
            col.sources.get("ttl", {}).os == "Linux"
        ),
        result={
            "os": "Linux",
            "model": "",
            "device_type": "Network Device",
            "vendor": "",
            "confidence": 60,
            "reason": "TTL=64 (Linux)"
        },
        priority=60
    ),
    
    # Windows device (TTL only)
    CorrelationRule(
        name="Windows Device",
        condition=lambda d, c, col: (
            c.icmp and 
            col.sources.get("ttl", {}).os == "Windows"
        ),
        result={
            "os": "Windows",
            "model": "",
            "device_type": "PC/Server",
            "vendor": "",
            "confidence": 60,
            "reason": "TTL=128 (Windows)"
        },
        priority=60
    ),
    
    # Silent IoT device
    CorrelationRule(
        name="Silent IoT Device",
        condition=lambda d, c, col: (
            not c.icmp and 
            not c.tcp and 
            d.flows > 0 and 
            d.megabytes < 10
        ),
        result={
            "os": "Unknown",
            "model": "",
            "device_type": "IoT Device",
            "vendor": d.vendor if d.vendor != "Unknown" else "",
            "confidence": 40,
            "reason": "Low traffic + no ICMP/TCP (sleeping IoT)"
        },
        priority=40
    ),
]


def apply_rules(device, capabilities: DeviceCapabilities, collected) -> dict | None:
    """
    Применяет все правила и возвращает лучшее совпадение.
    """
    matches = []
    
    for rule in RULES:
        try:
            if rule.condition(device, capabilities, collected):
                matches.append(rule)
        except Exception:
            continue
    
    if not matches:
        return None
    
    # Выбираем правило с наивысшим priority
    best = max(matches, key=lambda r: r.priority)
    return best.result
