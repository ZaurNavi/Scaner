#!/usr/bin/env python3
"""
Правила для IoT-устройств.
Только правила по TCP-портам и flows.
HTTP-правила находятся в http_devices.py.
"""

from .base import Rule


IOT_RULES = [

    # Silent IoT (есть трафик, но нет открытых TCP-портов)
    Rule(
        name="iot_silent",
        when=lambda e: (
            e.flows and
            not e.has_open_ports() and
            e.megabytes < 10 and
            not e.vendor  # Только если vendor неизвестен
        ),
        then={
            "os": "Unknown",
            "device_type": "IoT Device",
            "vendor": "",
            "confidence": 40,
            "reason": "Low traffic + no open TCP ports (sleeping IoT)"
        },
        priority=40
    ),

    # NAS (Synology) — по портам
    Rule(
        name="nas_synology",
        when=lambda e: e.has_port(5000) or e.has_port(5001),
        then={
            "os": "DSM",
            "device_type": "NAS",
            "vendor": "Synology",
            "confidence": 85,
            "reason": "Synology NAS ports detected"
        },
        priority=85
    ),

    # Chromecast — по портам
    Rule(
        name="chromecast",
        when=lambda e: e.has_port(8008) or e.has_port(8009),
        then={
            "os": "Chromecast OS",
            "device_type": "Media Player",
            "vendor": "Google",
            "confidence": 85,
            "reason": "Chromecast ports detected"
        },
        priority=85
    ),

    # Plex — по порту
    Rule(
        name="plex_server",
        when=lambda e: e.has_port(32400),
        then={
            "os": "Plex OS",
            "device_type": "Media Server",
            "vendor": "Plex",
            "confidence": 85,
            "reason": "Plex port 32400"
        },
        priority=85
    ),
]
