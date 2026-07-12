#!/usr/bin/env python3
"""
HTTP-сигнатуры для определения устройств.

Каждая сигнатура — это словарь с полями:
- field: что проверяем (server, title, body, url, header:X-Name)
- pattern: regex или substring
- vendor: производитель
- model: модель (может быть "")
- device_type: тип устройства
- os: ОС (может быть "")
- confidence: уверенность (0-100)
- reason: объяснение

Сигнатуры проверяются по порядку, первое совпадение побеждает.
Более специфичные сигнатуры должны идти раньше.
"""

from __future__ import annotations


# Формат сигнатуры
HTTP_SIGNATURES = [
    # ---------------------------------------------------------
    # OpenWrt / LuCI
    # ---------------------------------------------------------
    {
        "field": "body",
        "pattern": r"/cgi-bin/luci/",
        "vendor": "OpenWrt",
        "model": "",
        "device_type": "Router",
        "os": "OpenWrt",
        "confidence": 90,
        "reason": "LuCI web interface detected",
    },
    {
        "field": "title",
        "pattern": r"OpenWrt",
        "vendor": "OpenWrt",
        "model": "",
        "device_type": "Router",
        "os": "OpenWrt",
        "confidence": 85,
        "reason": "Title contains 'OpenWrt'",
    },

    # ---------------------------------------------------------
    # MikroTik RouterOS
    # ---------------------------------------------------------
    {
        "field": "header:WWW-Authenticate",
        "pattern": r"RouterOS",
        "vendor": "MikroTik",
        "model": "",
        "device_type": "Router",
        "os": "RouterOS",
        "confidence": 95,
        "reason": "RouterOS authentication detected",
    },
    {
        "field": "title",
        "pattern": r"RouterOS",
        "vendor": "MikroTik",
        "model": "",
        "device_type": "Router",
        "os": "RouterOS",
        "confidence": 90,
        "reason": "Title contains 'RouterOS'",
    },
    {
        "field": "server",
        "pattern": r"MikroTik",
        "vendor": "MikroTik",
        "model": "",
        "device_type": "Router",
        "os": "RouterOS",
        "confidence": 85,
        "reason": "Server header: MikroTik",
    },

    # ---------------------------------------------------------
    # Keenetic
    # ---------------------------------------------------------
    {
        "field": "title",
        "pattern": r"Keenetic",
        "vendor": "Keenetic",
        "model": "",
        "device_type": "Router",
        "os": "KeeneticOS",
        "confidence": 90,
        "reason": "Title contains 'Keenetic'",
    },
    {
        "field": "server",
        "pattern": r"Keenetic",
        "vendor": "Keenetic",
        "model": "",
        "device_type": "Router",
        "os": "KeeneticOS",
        "confidence": 85,
        "reason": "Server header: Keenetic",
    },

    # ---------------------------------------------------------
    # TP-Link
    # ---------------------------------------------------------
    {
        "field": "title",
        "pattern": r"TP-LINK",
        "vendor": "TP-Link",
        "model": "",
        "device_type": "Router",
        "os": "",
        "confidence": 85,
        "reason": "Title contains 'TP-LINK'",
    },
    {
        "field": "server",
        "pattern": r"TP-LINK",
        "vendor": "TP-Link",
        "model": "",
        "device_type": "Router",
        "os": "",
        "confidence": 80,
        "reason": "Server header: TP-LINK",
    },
    {
        "field": "body",
        "pattern": r"tplinklogin|tp-link\.com",
        "vendor": "TP-Link",
        "model": "",
        "device_type": "Router",
        "os": "",
        "confidence": 80,
        "reason": "TP-Link login page detected",
    },

    # ---------------------------------------------------------
    # Ubiquiti / UniFi
    # ---------------------------------------------------------
    {
        "field": "title",
        "pattern": r"UniFi",
        "vendor": "Ubiquiti",
        "model": "UniFi Controller",
        "device_type": "UniFi Controller",
        "os": "",
        "confidence": 90,
        "reason": "Title contains 'UniFi'",
    },
    {
        "field": "server",
        "pattern": r"ubnt",
        "vendor": "Ubiquiti",
        "model": "",
        "device_type": "Network Device",
        "os": "",
        "confidence": 80,
        "reason": "Server header: ubnt",
    },

    # ---------------------------------------------------------
    # Synology NAS
    # ---------------------------------------------------------
    {
        "field": "title",
        "pattern": r"Synology",
        "vendor": "Synology",
        "model": "",
        "device_type": "NAS",
        "os": "DSM",
        "confidence": 90,
        "reason": "Title contains 'Synology'",
    },
    {
        "field": "server",
        "pattern": r"synology",
        "vendor": "Synology",
        "model": "",
        "device_type": "NAS",
        "os": "DSM",
        "confidence": 85,
        "reason": "Server header: synology",
    },

    # ---------------------------------------------------------
    # QNAP NAS
    # ---------------------------------------------------------
    {
        "field": "title",
        "pattern": r"QNAP",
        "vendor": "QNAP",
        "model": "",
        "device_type": "NAS",
        "os": "QTS",
        "confidence": 90,
        "reason": "Title contains 'QNAP'",
    },

    # ---------------------------------------------------------
    # IP Cameras
    # ---------------------------------------------------------
    {
        "field": "server",
        "pattern": r"Hikvision",
        "vendor": "Hikvision",
        "model": "",
        "device_type": "IP Camera",
        "os": "",
        "confidence": 90,
        "reason": "Server header: Hikvision",
    },
    {
        "field": "title",
        "pattern": r"Hikvision",
        "vendor": "Hikvision",
        "model": "",
        "device_type": "IP Camera",
        "os": "",
        "confidence": 85,
        "reason": "Title contains 'Hikvision'",
    },
    {
        "field": "server",
        "pattern": r"Dahua|DVRDVS",
        "vendor": "Dahua",
        "model": "",
        "device_type": "IP Camera",
        "os": "",
        "confidence": 90,
        "reason": "Server header: Dahua/DVRDVS",
    },
    {
        "field": "title",
        "pattern": r"Dahua",
        "vendor": "Dahua",
        "model": "",
        "device_type": "IP Camera",
        "os": "",
        "confidence": 85,
        "reason": "Title contains 'Dahua'",
    },
    {
        "field": "body",
        "pattern": r"webLogin\.cgi|webguide/",
        "vendor": "IP Camera",
        "model": "",
        "device_type": "IP Camera",
        "os": "",
        "confidence": 60,
        "reason": "Camera login page detected",
    },

    # ---------------------------------------------------------
    # Принтеры
    # ---------------------------------------------------------
    {
        "field": "server",
        "pattern": r"HP-ILO|HP-ChaiServer",
        "vendor": "HP",
        "model": "",
        "device_type": "Printer",
        "os": "",
        "confidence": 85,
        "reason": "Server header: HP printer",
    },
    {
        "field": "title",
        "pattern": r"HP LaserJet|HP DesignJet",
        "vendor": "HP",
        "model": "",
        "device_type": "Printer",
        "os": "",
        "confidence": 90,
        "reason": "Title contains HP printer model",
    },
    {
        "field": "title",
        "pattern": r"Brother",
        "vendor": "Brother",
        "model": "",
        "device_type": "Printer",
        "os": "",
        "confidence": 90,
        "reason": "Title contains 'Brother'",
    },
    {
        "field": "server",
        "pattern": r"Brother",
        "vendor": "Brother",
        "model": "",
        "device_type": "Printer",
        "os": "",
        "confidence": 85,
        "reason": "Server header: Brother",
    },
    {
        "field": "title",
        "pattern": r"EPSON|Epson",
        "vendor": "Epson",
        "model": "",
        "device_type": "Printer",
        "os": "",
        "confidence": 90,
        "reason": "Title contains 'Epson'",
    },
    {
        "field": "title",
        "pattern": r"Canon",
        "vendor": "Canon",
        "model": "",
        "device_type": "Printer",
        "os": "",
        "confidence": 85,
        "reason": "Title contains 'Canon'",
    },

    # ---------------------------------------------------------
    # Generic web servers (низкий приоритет)
    # ---------------------------------------------------------
    {
        "field": "server",
        "pattern": r"GoAhead",
        "vendor": "",
        "model": "",
        "device_type": "Embedded Device",
        "os": "",
        "confidence": 40,
        "reason": "Server: GoAhead (embedded)",
    },
    {
        "field": "server",
        "pattern": r"lighttpd",
        "vendor": "",
        "model": "",
        "device_type": "Network Device",
        "os": "Linux",
        "confidence": 35,
        "reason": "Server: lighttpd",
    },
    {
        "field": "server",
        "pattern": r"mini_httpd",
        "vendor": "",
        "model": "",
        "device_type": "Embedded Device",
        "os": "Linux",
        "confidence": 35,
        "reason": "Server: mini_httpd",
    },
    {
        "field": "server",
        "pattern": r"Boa",
        "vendor": "",
        "model": "",
        "device_type": "Embedded Device",
        "os": "Linux",
        "confidence": 35,
        "reason": "Server: Boa",
    },
]
