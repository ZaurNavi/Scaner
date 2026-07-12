#!/usr/bin/env python3
"""
Правила для Apple-устройств.
"""

from .base import Rule


APPLE_RULES = [
    
    # iPhone (по hostname)
    Rule(
        name="apple_iphone",
        when=lambda e: "iphone" in e.hostname.lower(),
        then={
            "os": "iOS",
            "device_type": "Smartphone",
            "vendor": "Apple",
            "confidence": 85,
            "reason": "Hostname indicates iPhone"
        },
        priority=85
    ),
    
    # iPad
    Rule(
        name="apple_ipad",
        when=lambda e: "ipad" in e.hostname.lower(),
        then={
            "os": "iOS",
            "device_type": "Tablet",
            "vendor": "Apple",
            "confidence": 85,
            "reason": "Hostname indicates iPad"
        },
        priority=85
    ),
    
    # MacBook
    Rule(
        name="apple_macbook",
        when=lambda e: "macbook" in e.hostname.lower() or "imac" in e.hostname.lower(),
        then={
            "os": "macOS",
            "device_type": "Laptop",
            "vendor": "Apple",
            "confidence": 85,
            "reason": "Hostname indicates Mac"
        },
        priority=85
    ),
    
    # Apple (по vendor, silent)
    Rule(
        name="apple_silent",
        when=lambda e: (
            e.vendor and "apple" in e.vendor.lower() and
            not e.ping and
            not e.tcp_ports
        ),
        then={
            "os": "iOS/macOS",
            "device_type": "Apple Device",
            "vendor": "Apple",
            "confidence": 70,
            "reason": "Apple vendor + no ICMP/TCP (firewall)"
        },
        priority=70
    ),
    
    # Apple (по mDNS)
    Rule(
        name="apple_mdns",
        when=lambda e: e.mdns_device_type == "iPhone",
        then={
            "os": "iOS",
            "device_type": "Smartphone",
            "vendor": "Apple",
            "confidence": 85,
            "reason": "mDNS reports iPhone"
        },
        priority=85
    ),
]
