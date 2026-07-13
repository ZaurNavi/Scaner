#!/usr/bin/env python3
"""
Правила для определения устройств по SNMP данным.

Архитектура:
- Работают с Evidence.snmp_* полями
- SNMP — очень надёжный источник (высокий приоритет)
- Более специфичные правила (по sysObjectID) имеют больший приоритет
- Общие правила (по sysDescr) имеют средний приоритет
- Правила по sysServices имеют низкий приоритет
"""

from .base import Rule


SNMP_DEVICE_RULES = [

    # ---------------------------------------------------------
    # MikroTik RouterOS (по sysObjectID)
    # ---------------------------------------------------------
    Rule(
        name="snmp_mikrotik_routeros",
        when=lambda e: (
            e.snmp_responded and
            ".1.3.6.1.4.1.14988" in e.snmp_sys_object_id
        ),
        then={
            "os": "RouterOS",
            "device_type": "Router",
            "vendor": "MikroTik",
            "confidence": 95,
            "reason": "SNMP: MikroTik RouterOS"
        },
        priority=95
    ),

    # ---------------------------------------------------------
    # MikroTik RouterOS (по sysDescr)
    # ---------------------------------------------------------
    Rule(
        name="snmp_mikrotik_routeros_descr",
        when=lambda e: (
            e.snmp_responded and
            "routeros" in e.snmp_sys_descr.lower()
        ),
        then={
            "os": "RouterOS",
            "device_type": "Router",
            "vendor": "MikroTik",
            "confidence": 90,
            "reason": "SNMP: MikroTik RouterOS (sysDescr)"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Cisco IOS (по sysObjectID)
    # ---------------------------------------------------------
    Rule(
        name="snmp_cisco_ios",
        when=lambda e: (
            e.snmp_responded and
            ".1.3.6.1.4.1.9" in e.snmp_sys_object_id
        ),
        then={
            "os": "Cisco IOS",
            "device_type": "Network Device",
            "vendor": "Cisco",
            "confidence": 95,
            "reason": "SNMP: Cisco IOS"
        },
        priority=95
    ),

    # ---------------------------------------------------------
    # Cisco IOS (по sysDescr)
    # ---------------------------------------------------------
    Rule(
        name="snmp_cisco_ios_descr",
        when=lambda e: (
            e.snmp_responded and
            "cisco ios" in e.snmp_sys_descr.lower()
        ),
        then={
            "os": "Cisco IOS",
            "device_type": "Network Device",
            "vendor": "Cisco",
            "confidence": 90,
            "reason": "SNMP: Cisco IOS (sysDescr)"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # QNAP NAS (по sysDescr)
    # ---------------------------------------------------------
    Rule(
        name="snmp_qnap_nas",
        when=lambda e: (
            e.snmp_responded and
            "qnap" in e.snmp_sys_descr.lower()
        ),
        then={
            "os": "QTS",
            "device_type": "NAS",
            "vendor": "QNAP",
            "confidence": 95,
            "reason": "SNMP: QNAP NAS"
        },
        priority=95
    ),

    # ---------------------------------------------------------
    # Synology NAS (по sysDescr)
    # ---------------------------------------------------------
    Rule(
        name="snmp_synology_nas",
        when=lambda e: (
            e.snmp_responded and
            "synology" in e.snmp_sys_descr.lower()
        ),
        then={
            "os": "DSM",
            "device_type": "NAS",
            "vendor": "Synology",
            "confidence": 95,
            "reason": "SNMP: Synology NAS"
        },
        priority=95
    ),

    # ---------------------------------------------------------
    # HP Printer (по sysDescr)
    # ---------------------------------------------------------
    Rule(
        name="snmp_hp_printer",
        when=lambda e: (
            e.snmp_responded and
            ("hp" in e.snmp_sys_descr.lower() or
             "hewlett-packard" in e.snmp_sys_descr.lower())
        ),
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "HP",
            "confidence": 90,
            "reason": "SNMP: HP printer"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Brother Printer (по sysDescr)
    # ---------------------------------------------------------
    Rule(
        name="snmp_brother_printer",
        when=lambda e: (
            e.snmp_responded and
            "brother" in e.snmp_sys_descr.lower()
        ),
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "Brother",
            "confidence": 90,
            "reason": "SNMP: Brother printer"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Epson Printer (по sysDescr)
    # ---------------------------------------------------------
    Rule(
        name="snmp_epson_printer",
        when=lambda e: (
            e.snmp_responded and
            "epson" in e.snmp_sys_descr.lower()
        ),
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "Epson",
            "confidence": 90,
            "reason": "SNMP: Epson printer"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Canon Printer (по sysDescr)
    # ---------------------------------------------------------
    Rule(
        name="snmp_canon_printer",
        when=lambda e: (
            e.snmp_responded and
            "canon" in e.snmp_sys_descr.lower()
        ),
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "Canon",
            "confidence": 90,
            "reason": "SNMP: Canon printer"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Linux (по sysDescr)
    # ---------------------------------------------------------
    Rule(
        name="snmp_linux",
        when=lambda e: (
            e.snmp_responded and
            "linux" in e.snmp_sys_descr.lower()
        ),
        then={
            "os": "Linux",
            "device_type": "Unknown",
            "vendor": "",
            "confidence": 70,
            "reason": "SNMP: Linux device"
        },
        priority=70
    ),

    # ---------------------------------------------------------
    # Windows (по sysDescr)
    # ---------------------------------------------------------
    Rule(
        name="snmp_windows",
        when=lambda e: (
            e.snmp_responded and
            "windows" in e.snmp_sys_descr.lower()
        ),
        then={
            "os": "Windows",
            "device_type": "Unknown",
            "vendor": "",
            "confidence": 70,
            "reason": "SNMP: Windows device"
        },
        priority=70
    ),

    # ---------------------------------------------------------
    # Router (по sysServices == 72)
    # ---------------------------------------------------------
    Rule(
        name="snmp_router_by_services",
        when=lambda e: (
            e.snmp_responded and
            e.snmp_sys_services == 72
        ),
        then={
            "os": "Unknown",
            "device_type": "Router",
            "vendor": "",
            "confidence": 60,
            "reason": "SNMP: sysServices=72 (router)"
        },
        priority=60
    ),

    # ---------------------------------------------------------
    # Switch (по sysServices == 76)
    # ---------------------------------------------------------
    Rule(
        name="snmp_switch_by_services",
        when=lambda e: (
            e.snmp_responded and
            e.snmp_sys_services == 76
        ),
        then={
            "os": "Unknown",
            "device_type": "Switch",
            "vendor": "",
            "confidence": 60,
            "reason": "SNMP: sysServices=76 (switch)"
        },
        priority=60
    ),

    # ---------------------------------------------------------
    # Generic SNMP device (низкий приоритет)
    # ---------------------------------------------------------
    Rule(
        name="snmp_generic",
        when=lambda e: e.snmp_responded,
        then={
            "os": "Unknown",
            "device_type": "Unknown",
            "vendor": "",
            "confidence": 40,
            "reason": "SNMP: generic device"
        },
        priority=40
    ),
]
