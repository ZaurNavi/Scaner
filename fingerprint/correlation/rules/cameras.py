#!/usr/bin/env python3
"""
Правила для IP-камер.
Только правила по TCP-портам.
HTTP-правила находятся в http_devices.py.
"""

from .base import Rule


CAMERA_RULES = [

    # IP Camera (RTSP)
    Rule(
        name="ip_camera_rtsp",
        when=lambda e: e.has_port(554),
        then={
            "os": "Embedded Linux",
            "device_type": "IP Camera",
            "vendor": "",
            "confidence": 85,
            "reason": "RTSP port 554"
        },
        priority=85
    ),
]
