#!/usr/bin/env python3
"""
Правила для определения устройств по SSDP/UPnP данным.

Архитектура:
- Работают с Evidence.ssdp_* полями
- Более специфичные правила (по manufacturer/model_name) имеют больший приоритет
- Общие правила (по server) имеют низкий приоритет
"""

from .base import Rule


SSDP_DEVICE_RULES = [

    # ---------------------------------------------------------
    # Smart TV — Samsung
    # ---------------------------------------------------------
    Rule(
        name="ssdp_samsung_tv",
        when=lambda e: (
            e.ssdp_responded and
            ("samsung" in e.ssdp_manufacturer.lower() or
             "samsung" in e.ssdp_server.lower() or
             "samsung" in e.ssdp_friendly_name.lower())
        ),
        then={
            "os": "Tizen",
            "device_type": "Smart TV",
            "vendor": "Samsung",
            "confidence": 90,
            "reason": "SSDP: Samsung Smart TV"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Smart TV — LG
    # ---------------------------------------------------------
    Rule(
        name="ssdp_lg_tv",
        when=lambda e: (
            e.ssdp_responded and
            ("lg" in e.ssdp_manufacturer.lower() or
             "LG" in e.ssdp_server or
             "webos" in e.ssdp_server.lower() or
             "lg" in e.ssdp_friendly_name.lower())
        ),
        then={
            "os": "webOS",
            "device_type": "Smart TV",
            "vendor": "LG",
            "confidence": 90,
            "reason": "SSDP: LG Smart TV"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Smart TV — Sony
    # ---------------------------------------------------------
    Rule(
        name="ssdp_sony_tv",
        when=lambda e: (
            e.ssdp_responded and
            ("sony" in e.ssdp_manufacturer.lower() or
             "sony" in e.ssdp_server.lower())
        ),
        then={
            "os": "Android TV",
            "device_type": "Smart TV",
            "vendor": "Sony",
            "confidence": 85,
            "reason": "SSDP: Sony Smart TV"
        },
        priority=85
    ),

    # ---------------------------------------------------------
    # Smart TV — Philips
    # ---------------------------------------------------------
    Rule(
        name="ssdp_philips_tv",
        when=lambda e: (
            e.ssdp_responded and
            ("philips" in e.ssdp_manufacturer.lower() or
             "philips" in e.ssdp_server.lower())
        ),
        then={
            "os": "Android TV",
            "device_type": "Smart TV",
            "vendor": "Philips",
            "confidence": 85,
            "reason": "SSDP: Philips Smart TV"
        },
        priority=85
    ),

    # ---------------------------------------------------------
    # Android TV / Google TV
    # ---------------------------------------------------------
    Rule(
        name="ssdp_android_tv",
        when=lambda e: (
            e.ssdp_responded and
            ("android" in e.ssdp_model_name.lower() or
             "google" in e.ssdp_manufacturer.lower() or
             "bravia" in e.ssdp_model_name.lower())
        ),
        then={
            "os": "Android TV",
            "device_type": "Smart TV",
            "vendor": "Google",
            "confidence": 85,
            "reason": "SSDP: Android TV"
        },
        priority=85
    ),

    # ---------------------------------------------------------
    # Chromecast
    # ---------------------------------------------------------
    Rule(
        name="ssdp_chromecast",
        when=lambda e: (
            e.ssdp_responded and
            ("chromecast" in e.ssdp_model_name.lower() or
             "chromecast" in e.ssdp_friendly_name.lower() or
             "eureka" in e.ssdp_server.lower())
        ),
        then={
            "os": "Chromecast OS",
            "device_type": "Media Player",
            "vendor": "Google",
            "confidence": 90,
            "reason": "SSDP: Chromecast"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Apple TV
    # ---------------------------------------------------------
    Rule(
        name="ssdp_apple_tv",
        when=lambda e: (
            e.ssdp_responded and
            ("apple tv" in e.ssdp_model_name.lower() or
             "appletv" in e.ssdp_model_name.lower() or
             "apple" in e.ssdp_manufacturer.lower())
        ),
        then={
            "os": "tvOS",
            "device_type": "Media Player",
            "vendor": "Apple",
            "confidence": 90,
            "reason": "SSDP: Apple TV"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Roku
    # ---------------------------------------------------------
    Rule(
        name="ssdp_roku",
        when=lambda e: (
            e.ssdp_responded and
            ("roku" in e.ssdp_manufacturer.lower() or
             "roku" in e.ssdp_model_name.lower())
        ),
        then={
            "os": "Roku OS",
            "device_type": "Media Player",
            "vendor": "Roku",
            "confidence": 90,
            "reason": "SSDP: Roku"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Amazon Fire TV
    # ---------------------------------------------------------
    Rule(
        name="ssdp_fire_tv",
        when=lambda e: (
            e.ssdp_responded and
            ("fire tv" in e.ssdp_model_name.lower() or
             "aft" in e.ssdp_model_name.lower() or
             "amazon" in e.ssdp_manufacturer.lower())
        ),
        then={
            "os": "Fire OS",
            "device_type": "Media Player",
            "vendor": "Amazon",
            "confidence": 85,
            "reason": "SSDP: Amazon Fire TV"
        },
        priority=85
    ),

    # ---------------------------------------------------------
    # Sonos
    # ---------------------------------------------------------
    Rule(
        name="ssdp_sonos",
        when=lambda e: (
            e.ssdp_responded and
            ("sonos" in e.ssdp_manufacturer.lower() or
             "sonos" in e.ssdp_model_name.lower())
        ),
        then={
            "os": "Sonos OS",
            "device_type": "Speaker",
            "vendor": "Sonos",
            "confidence": 90,
            "reason": "SSDP: Sonos speaker"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Игровые консоли — Xbox
    # ---------------------------------------------------------
    Rule(
        name="ssdp_xbox",
        when=lambda e: (
            e.ssdp_responded and
            ("xbox" in e.ssdp_model_name.lower() or
             "microsoft" in e.ssdp_manufacturer.lower())
        ),
        then={
            "os": "Xbox OS",
            "device_type": "Game Console",
            "vendor": "Microsoft",
            "confidence": 90,
            "reason": "SSDP: Xbox"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Игровые консоли — PlayStation
    # ---------------------------------------------------------
    Rule(
        name="ssdp_playstation",
        when=lambda e: (
            e.ssdp_responded and
            ("playstation" in e.ssdp_model_name.lower() or
             "ps4" in e.ssdp_model_name.lower() or
             "ps5" in e.ssdp_model_name.lower() or
             "sony computer" in e.ssdp_manufacturer.lower())
        ),
        then={
            "os": "PlayStation OS",
            "device_type": "Game Console",
            "vendor": "Sony",
            "confidence": 90,
            "reason": "SSDP: PlayStation"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # IP Cameras — Hikvision
    # ---------------------------------------------------------
    Rule(
        name="ssdp_hikvision_camera",
        when=lambda e: (
            e.ssdp_responded and
            ("hikvision" in e.ssdp_manufacturer.lower() or
             "hikvision" in e.ssdp_server.lower())
        ),
        then={
            "os": "Hikvision OS",
            "device_type": "IP Camera",
            "vendor": "Hikvision",
            "confidence": 95,
            "reason": "SSDP: Hikvision camera"
        },
        priority=95
    ),

    # ---------------------------------------------------------
    # IP Cameras — Dahua
    # ---------------------------------------------------------
    Rule(
        name="ssdp_dahua_camera",
        when=lambda e: (
            e.ssdp_responded and
            ("dahua" in e.ssdp_manufacturer.lower() or
             "dahua" in e.ssdp_server.lower())
        ),
        then={
            "os": "Dahua OS",
            "device_type": "IP Camera",
            "vendor": "Dahua",
            "confidence": 95,
            "reason": "SSDP: Dahua camera"
        },
        priority=95
    ),

    # ---------------------------------------------------------
    # Принтеры — HP
    # ---------------------------------------------------------
    Rule(
        name="ssdp_hp_printer",
        when=lambda e: (
            e.ssdp_responded and
            ("hp" in e.ssdp_manufacturer.lower() or
             "hewlett-packard" in e.ssdp_manufacturer.lower())
        ),
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "HP",
            "confidence": 90,
            "reason": "SSDP: HP printer"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Принтеры — Brother
    # ---------------------------------------------------------
    Rule(
        name="ssdp_brother_printer",
        when=lambda e: (
            e.ssdp_responded and
            ("brother" in e.ssdp_manufacturer.lower() or
             "brother" in e.ssdp_model_name.lower())
        ),
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "Brother",
            "confidence": 90,
            "reason": "SSDP: Brother printer"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Принтеры — Epson
    # ---------------------------------------------------------
    Rule(
        name="ssdp_epson_printer",
        when=lambda e: (
            e.ssdp_responded and
            ("epson" in e.ssdp_manufacturer.lower() or
             "epson" in e.ssdp_model_name.lower())
        ),
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "Epson",
            "confidence": 90,
            "reason": "SSDP: Epson printer"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Принтеры — Canon
    # ---------------------------------------------------------
    Rule(
        name="ssdp_canon_printer",
        when=lambda e: (
            e.ssdp_responded and
            ("canon" in e.ssdp_manufacturer.lower() or
             "canon" in e.ssdp_model_name.lower())
        ),
        then={
            "os": "Embedded",
            "device_type": "Printer",
            "vendor": "Canon",
            "confidence": 90,
            "reason": "SSDP: Canon printer"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # NAS — Synology
    # ---------------------------------------------------------
    Rule(
        name="ssdp_synology_nas",
        when=lambda e: (
            e.ssdp_responded and
            ("synology" in e.ssdp_manufacturer.lower() or
             "synology" in e.ssdp_model_name.lower())
        ),
        then={
            "os": "DSM",
            "device_type": "NAS",
            "vendor": "Synology",
            "confidence": 90,
            "reason": "SSDP: Synology NAS"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # NAS — QNAP
    # ---------------------------------------------------------
    Rule(
        name="ssdp_qnap_nas",
        when=lambda e: (
            e.ssdp_responded and
            ("qnap" in e.ssdp_manufacturer.lower() or
             "qnap" in e.ssdp_model_name.lower())
        ),
        then={
            "os": "QTS",
            "device_type": "NAS",
            "vendor": "QNAP",
            "confidence": 90,
            "reason": "SSDP: QNAP NAS"
        },
        priority=90
    ),

    # ---------------------------------------------------------
    # Xiaomi IoT
    # ---------------------------------------------------------
    Rule(
        name="ssdp_xiaomi_iot",
        when=lambda e: (
            e.ssdp_responded and
            ("xiaomi" in e.ssdp_manufacturer.lower() or
             "xiaomi" in e.ssdp_model_name.lower())
        ),
        then={
            "os": "Xiaomi IoT",
            "device_type": "IoT Device",
            "vendor": "Xiaomi",
            "confidence": 85,
            "reason": "SSDP: Xiaomi IoT device"
        },
        priority=85
    ),

    # ---------------------------------------------------------
    # TP-Link IoT
    # ---------------------------------------------------------
    Rule(
        name="ssdp_tplink_iot",
        when=lambda e: (
            e.ssdp_responded and
            ("tp-link" in e.ssdp_manufacturer.lower() or
             "tplink" in e.ssdp_manufacturer.lower())
        ),
        then={
            "os": "TP-Link IoT",
            "device_type": "IoT Device",
            "vendor": "TP-Link",
            "confidence": 85,
            "reason": "SSDP: TP-Link IoT device"
        },
        priority=85
    ),

    # ---------------------------------------------------------
    # Generic DLNA (низкий приоритет)
    # ---------------------------------------------------------
    Rule(
        name="ssdp_dlna_generic",
        when=lambda e: (
            e.ssdp_responded and
            ("dlna" in e.ssdp_st.lower() or
             "media renderer" in e.ssdp_st.lower() or
             "media server" in e.ssdp_st.lower())
        ),
        then={
            "os": "Unknown",
            "device_type": "DLNA Device",
            "vendor": "",
            "confidence": 50,
            "reason": "SSDP: DLNA device"
        },
        priority=50
    ),

    # ---------------------------------------------------------
    # Generic UPnP (очень низкий приоритет)
    # ---------------------------------------------------------
    Rule(
        name="ssdp_upnp_generic",
        when=lambda e: e.ssdp_responded,
        then={
            "os": "Unknown",
            "device_type": "UPnP Device",
            "vendor": "",
            "confidence": 30,
            "reason": "SSDP: UPnP device"
        },
        priority=30
    ),
]
