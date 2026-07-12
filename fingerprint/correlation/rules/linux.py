#!/usr/bin/env python3
"""
Правила для Linux-устройств.
"""

from .base import Rule


LINUX_RULES = [

    # Linux (по TTL + vendor = вероятно Android)
    Rule(
        name="linux_vendor_silent",
        when=lambda e: (
            e.ttl and 55 <= e.ttl <= 64 and
            e.vendor and e.vendor != "Unknown" and
            not e.has_open_ports()
        ),
        then={
            "os": "Android",
            "device_type": "Smartphone",
            "vendor": "",
            "confidence": 65,
            "reason": "Vendor + TTL=64 + no open TCP ports (likely Android)"
        },
        priority=65
    ),

    # Linux (по TTL, без vendor) — НИЗКИЙ приоритет
    Rule(
        name="linux_ttl_generic",
        when=lambda e: e.ttl and 55 <= e.ttl <= 64,
        then={
            "os": "Linux",
            "device_type": "Network Device",
            "vendor": "",
            "confidence": 40,
            "reason": "TTL=55-64 (Linux)"
        },
        priority=40
    ),

    # Linux (по hostname)
    Rule(
        name="linux_hostname",
        when=lambda e: "linux" in e.hostname.lower() or "ubuntu" in e.hostname.lower(),
        then={
            "os": "Linux",
            "device_type": "Server",
            "vendor": "",
            "confidence": 70,
            "reason": "Hostname indicates Linux"
        },
        priority=70
    ),

    # SSH (вероятно Linux)
    Rule(
        name="linux_ssh",
        when=lambda e: e.has_port(22) and not e.has_port(80),
        then={
            "os": "Linux",
            "device_type": "Server",
            "vendor": "",
            "confidence": 55,
            "reason": "SSH port 22"
        },
        priority=55
    ),
]
