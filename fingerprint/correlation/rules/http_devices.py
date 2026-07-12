#!/usr/bin/env python3
"""
Правила для определения устройств по HTTP-заголовкам и контенту.
"""

from .base import Rule


HTTP_DEVICE_RULES = [
    
    # ---------------------------------------------------------
    # OpenWrt / LuCI
    # ---------------------------------------------------------
    Rule(
        name="openwrt_luci",
        when=lambda e: "/cgi-bin/luci/" in e.http_body,
        then={
            "os": "OpenWrt",
            "device_type": "Router",
            "vendor": "OpenWrt",
            "confidence": 90,
            "reason": "LuCI web interface detected"
        },
        priority=90
    ),
    
    Rule(
        name="openwrt_title",
        when=lambda e: "OpenWrt" in e.http_title,
        then={
            "os": "OpenWrt",
            "device_type": "Router",
            "vendor": "OpenWrt",
            "confidence": 85,
            "reason": "Title contains 'OpenWrt'"
        },
        priority=85
    ),
    
    # ---------------------------------------------------------
    # MikroTik RouterOS
    # ---------------------------------------------------------
    Rule(
        name="mikrotik_http_auth",
        when=lambda e: "RouterOS" in e.http_server or "RouterOS" in e.http_title,
        then={
            "os": "RouterOS",
            "device_type": "Router",
            "vendor": "MikroTik",
            "confidence": 95,
            "reason": "RouterOS HTTP detected"
        },
        priority=95
    ),
    
    Rule(
        name="mikrotik_http_server",
        when=lambda e: "MikroTik" in e.http_server,
        then={
            "os": "RouterOS",
            "device_type": "Router",
            "vendor": "MikroTik",
            "confidence": 90,
            "reason": "Server header: MikroTik"
        },
        priority=90
    ),
    
    # ---------------------------------------------------------
    # Keenetic
    # ---------------------------------------------------------
    Rule(
        name="keenetic_http",
        when=lambda e: "Keenetic" in e.http_title or "keenetic" in e.http_server.lower(),
        then={
            "os": "KeeneticOS",
            "device_type": "Router",
            "vendor": "Keenetic",
            "confidence": 90,
            "reason": "Keenetic web interface detected"
        },
        priority=90
    ),
    
    # ---------------------------------------------------------
    # TP-Link
    # ---------------------------------------------------------
    Rule(
        name="tplink_http",
        when=lambda e: "TP-LINK" in e.http_title or "tp-link" in e.http_server.lower(),
        then={
            "os": "",
            "device_type": "Router",
            "vendor": "TP-Link",
            "confidence": 85,
            "reason": "TP-Link web interface detected"
        },
        priority=85
    ),
    
    Rule(
        name="tplink_body",
        when=lambda e: "tplinklogin" in e.http_body.lower() or "tp-link.com" in e.http_body.lower(),
        then={
            "os": "",
            "device_type": "Router",
            "vendor": "TP-Link",
            "confidence": 80,
            "reason": "TP-Link login page detected"
        },
        priority=80
    ),
    
    # ---------------------------------------------------------
    # Ubiquiti / UniFi
    # ---------------------------------------------------------
    Rule(
        name="unifi_http",
        when=lambda e: "UniFi" in e.http_title,
        then={
            "os": "UniFi OS",
            "device_type": "UniFi Controller",
            "vendor": "Ubiquiti",
            "confidence": 90,
            "reason": "UniFi Controller web interface"
        },
        priority=90
    ),
    
    Rule(
        name="ubnt_http",
        when=lambda e: "ubnt" in e.http_server.lower(),
        then={
            "os": "",
            "device_type": "Network Device",
            "vendor": "Ubiquiti",
            "confidence": 80,
            "reason": "Server header: ubnt"
        },
        priority=80
    ),
    
    # ---------------------------------------------------------
    # Synology NAS
    # ---------------------------------------------------------
    Rule(
        name="synology_http",
        when=lambda e: "Synology" in e.http_title or "synology" in e.http_server.lower(),
        then={
            "os": "DSM",
            "device_type": "NAS",
            "vendor": "Synology",
            "confidence": 90,
            "reason": "Synology web interface detected"
        },
        priority=90
    ),
    
    # ---------------------------------------------------------
    # QNAP NAS
    # ---------------------------------------------------------
    Rule(
        name="qnap_http",
        when=lambda e: "QNAP" in e.http_title,
        then={
            "os": "QTS",
            "device_type": "NAS",
            "vendor": "QNAP",
            "confidence": 90,
            "reason": "QNAP web interface detected"
        },
        priority=90
    ),
    
    # ---------------------------------------------------------
    # IP Cameras
    # ---------------------------------------------------------
    Rule(
        name="hikvision_http",
        when=lambda e: "Hikvision" in e.http_server or "Hikvision" in e.http_title,
        then={
            "os": "Hikvision OS",
            "device_type": "IP Camera",
            "vendor": "Hikvision",
            "confidence": 95,
            "reason": "Hikvision camera detected"
        },
        priority=95
    ),
    
    Rule(
        name="dahua_http",
        when=lambda e: "Dahua" in e.http_server or "Dahua" in e.http_title or "DVRDVS" in e.http_server,
        then={
            "os": "Dahua OS",
            "device_type": "IP Camera",
            "vendor": "Dahua",
            "confidence": 95,
            "reason": "Dahua camera detected"
        },
        priority=95
    ),
    
    # ---------------------------------------------------------
    # Принтеры
    # ---------------------------------------------------------
    Rule(
        name="hp_printer_http",
        when=lambda e: "HP" in e.http_title or "HP" in e.http_server,
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "HP",
            "confidence": 90,
            "reason": "HP printer detected"
        },
        priority=90
    ),
    
    Rule(
        name="brother_printer_http",
        when=lambda e: "Brother" in e.http_title or "Brother" in e.http_server,
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "Brother",
            "confidence": 90,
            "reason": "Brother printer detected"
        },
        priority=90
    ),
    
    Rule(
        name="epson_printer_http",
        when=lambda e: "Epson" in e.http_title or "EPSON" in e.http_title,
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "Epson",
            "confidence": 90,
            "reason": "Epson printer detected"
        },
        priority=90
    ),
    
    Rule(
        name="canon_printer_http",
        when=lambda e: "Canon" in e.http_title,
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "Canon",
            "confidence": 90,
            "reason": "Canon printer detected"
        },
        priority=90
    ),
    
    # ---------------------------------------------------------
    # Generic embedded web servers (низкий приоритет)
    # ---------------------------------------------------------
    Rule(
        name="embedded_goahead",
        when=lambda e: "GoAhead" in e.http_server,
        then={
            "os": "Embedded",
            "device_type": "Network Device",
            "vendor": "",
            "confidence": 40,
            "reason": "Server: GoAhead (embedded)"
        },
        priority=40
    ),
    
    Rule(
        name="embedded_lighttpd",
        when=lambda e: "lighttpd" in e.http_server.lower(),
        then={
            "os": "Linux",
            "device_type": "Network Device",
            "vendor": "",
            "confidence": 35,
            "reason": "Server: lighttpd"
        },
        priority=35
    ),
    
    Rule(
        name="embedded_mini_httpd",
        when=lambda e: "mini_httpd" in e.http_server.lower(),
        then={
            "os": "Linux",
            "device_type": "Network Device",
            "vendor": "",
            "confidence": 35,
            "reason": "Server: mini_httpd"
        },
        priority=35
    ),
    
    Rule(
        name="embedded_boa",
        when=lambda e: "Boa" in e.http_server,
        then={
            "os": "Linux",
            "device_type": "Network Device",
            "vendor": "",
            "confidence": 35,
            "reason": "Server: Boa"
        },
        priority=35
    ),
]
