#!/usr/bin/env python3
"""
Правила для Android-устройств.
"""

from .base import Rule


def _has_http_ports(e) -> bool:
    """Проверяет, открыты ли HTTP-порты (80, 443, 8080, 8443)."""
    http_ports = [80, 443, 8080, 8443]
    return any(e.has_port(p) for p in http_ports)


ANDROID_RULES = [

    # Xiaomi (без HTTP-портов, есть трафик) — ЛЮБЫЕ другие открытые порты допустимы
    Rule(
        name="android_xiaomi",
        when=lambda e: (
            e.vendor and "xiaomi" in e.vendor.lower() and
            e.flows and
            not _has_http_ports(e)
        ),
        then={
            "os": "Android",
            "device_type": "Smartphone",
            "vendor": "Xiaomi",
            "confidence": 70,
            "reason": "Xiaomi vendor + no HTTP ports (Android firewall)"
        },
        priority=70
    ),

    # Samsung (без HTTP-портов, есть трафик)
    Rule(
        name="android_samsung",
        when=lambda e: (
            e.vendor and "samsung" in e.vendor.lower() and
            e.flows and
            not _has_http_ports(e)
        ),
        then={
            "os": "Android",
            "device_type": "Smartphone",
            "vendor": "Samsung",
            "confidence": 70,
            "reason": "Samsung vendor + no HTTP ports (Android firewall)"
        },
        priority=70
    ),

    # Huawei (без HTTP-портов, есть трафик)
    Rule(
        name="android_huawei",
        when=lambda e: (
            e.vendor and "huawei" in e.vendor.lower() and
            e.flows and
            not _has_http_ports(e)
        ),
        then={
            "os": "Android",
            "device_type": "Smartphone",
            "vendor": "Huawei",
            "confidence": 70,
            "reason": "Huawei vendor + no HTTP ports (Android firewall)"
        },
        priority=70
    ),

    # Redmi/Poco (по hostname)
    Rule(
        name="android_redmi_poco",
        when=lambda e: (
            "redmi" in e.hostname.lower() or
            "poco" in e.hostname.lower() or
            "mi-" in e.hostname.lower()
        ),
        then={
            "os": "Android",
            "device_type": "Smartphone",
            "vendor": "Xiaomi",
            "confidence": 75,
            "reason": "Hostname indicates Xiaomi device"
        },
        priority=75
    ),

    # Samsung (по hostname)
    Rule(
        name="android_samsung_hostname",
        when=lambda e: "galaxy" in e.hostname.lower() or "samsung" in e.hostname.lower(),
        then={
            "os": "Android",
            "device_type": "Smartphone",
            "vendor": "Samsung",
            "confidence": 75,
            "reason": "Hostname indicates Samsung device"
        },
        priority=75
    ),

    # Pixel
    Rule(
        name="android_pixel",
        when=lambda e: "pixel" in e.hostname.lower(),
        then={
            "os": "Android",
            "device_type": "Smartphone",
            "vendor": "Google",
            "confidence": 80,
            "reason": "Hostname indicates Pixel device"
        },
        priority=80
    ),

    # Android (по hostname)
    Rule(
        name="android_generic",
        when=lambda e: "android" in e.hostname.lower(),
        then={
            "os": "Android",
            "device_type": "Smartphone",
            "vendor": "",
            "confidence": 70,
            "reason": "Hostname contains 'android'"
        },
        priority=70
    ),

    # Android (по mDNS)
    Rule(
        name="android_mdns",
        when=lambda e: e.mdns_device_type == "Android Device",
        then={
            "os": "Android",
            "device_type": "Smartphone",
            "vendor": "",
            "confidence": 80,
            "reason": "mDNS reports Android Device"
        },
        priority=80
    ),
]
