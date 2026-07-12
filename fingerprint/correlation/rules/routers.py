#!/usr/bin/env python3
"""
Правила для роутеров и сетевого оборудования.
Только правила по TCP-портам.
HTTP-правила находятся в http_devices.py.
"""

from .base import Rule


ROUTER_RULES = [

    # MikroTik RouterOS (по портам Winbox + API)
    Rule(
        name="mikrotik_routeros",
        when=lambda e: e.has_port(8291) and e.has_port(8728),
        then={
            "os": "RouterOS",
            "device_type": "Router",
            "vendor": "MikroTik",
            "confidence": 95,
            "reason": "MikroTik ports 8291 + 8728 detected"
        },
        priority=95
    ),

    # MikroTik (только Winbox)
    Rule(
        name="mikrotik_winbox",
        when=lambda e: e.has_port(8291),
        then={
            "os": "RouterOS",
            "device_type": "Router",
            "vendor": "MikroTik",
            "confidence": 85,
            "reason": "MikroTik Winbox port 8291"
        },
        priority=85
    ),

    # MikroTik (только API)
    Rule(
        name="mikrotik_api",
        when=lambda e: e.has_port(8728),
        then={
            "os": "RouterOS",
            "device_type": "Router",
            "vendor": "MikroTik",
            "confidence": 80,
            "reason": "MikroTik API port 8728"
        },
        priority=80
    ),

    # UniFi Controller
    Rule(
        name="unifi_controller",
        when=lambda e: e.has_port(8080) and e.has_port(8443),
        then={
            "os": "UniFi OS",
            "device_type": "UniFi Controller",
            "vendor": "Ubiquiti",
            "confidence": 90,
            "reason": "UniFi Controller ports 8080 + 8443"
        },
        priority=90
    ),

    # SSH + HTTP = вероятно Linux роутер
    Rule(
        name="linux_router_ssh_http",
        when=lambda e: e.has_port(22) and e.has_port(80) and e.ttl and 55 <= e.ttl <= 64,
        then={
            "os": "Linux",
            "device_type": "Router",
            "vendor": "",
            "confidence": 60,
            "reason": "SSH + HTTP + TTL=64 (Linux router)"
        },
        priority=60
    ),
]
