#!/usr/bin/env python3
"""
Правила для Windows-устройств.
"""

from .base import Rule


WINDOWS_RULES = [

    # Windows (RDP + SMB)
    Rule(
        name="windows_rdp_smb",
        when=lambda e: e.has_port(3389) and e.has_port(445),
        then={
            "os": "Windows",
            "device_type": "PC/Server",
            "vendor": "Microsoft",
            "confidence": 90,
            "reason": "RDP + SMB ports (3389 + 445)"
        },
        priority=90
    ),

    # Windows (RDP)
    Rule(
        name="windows_rdp",
        when=lambda e: e.has_port(3389),
        then={
            "os": "Windows",
            "device_type": "PC/Server",
            "vendor": "Microsoft",
            "confidence": 80,
            "reason": "RDP port 3389"
        },
        priority=80
    ),

    # Windows (SMB)
    Rule(
        name="windows_smb",
        when=lambda e: e.has_port(445),
        then={
            "os": "Windows",
            "device_type": "PC/Server",
            "vendor": "Microsoft",
            "confidence": 75,
            "reason": "SMB port 445"
        },
        priority=75
    ),

    # Windows (по hostname)
    Rule(
        name="windows_hostname",
        when=lambda e: (
            "desktop" in e.hostname.lower() or
            "laptop" in e.hostname.lower() or
            e.hostname.lower().startswith("pc-")
        ),
        then={
            "os": "Windows",
            "device_type": "PC",
            "vendor": "",
            "confidence": 60,
            "reason": "Hostname indicates Windows PC"
        },
        priority=60
    ),

    # Windows (по TTL)
    Rule(
        name="windows_ttl",
        when=lambda e: e.ttl and 115 <= e.ttl <= 128,
        then={
            "os": "Windows",
            "device_type": "PC/Server",
            "vendor": "",
            "confidence": 50,
            "reason": "TTL=115-128 (Windows)"
        },
        priority=50
    ),
]
