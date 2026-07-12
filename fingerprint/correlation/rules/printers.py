#!/usr/bin/env python3
"""
Правила для принтеров.
Только правила по TCP-портам.
HTTP-правила находятся в http_devices.py.
"""

from .base import Rule


PRINTER_RULES = [

    # Принтер (RAW + IPP)
    Rule(
        name="printer_raw_ipp",
        when=lambda e: e.has_port(9100) and e.has_port(631),
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "",
            "confidence": 90,
            "reason": "Printer ports 9100 + 631"
        },
        priority=90
    ),

    # Принтер (RAW)
    Rule(
        name="printer_raw",
        when=lambda e: e.has_port(9100),
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "",
            "confidence": 80,
            "reason": "RAW print port 9100"
        },
        priority=80
    ),

    # Принтер (IPP)
    Rule(
        name="printer_ipp",
        when=lambda e: e.has_port(631),
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "",
            "confidence": 75,
            "reason": "IPP port 631"
        },
        priority=75
    ),
]
