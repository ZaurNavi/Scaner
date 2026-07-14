#!/usr/bin/env python3
"""
MAC Vendor Intelligence — умное обогащение данных о производителе по MAC.
"""

from __future__ import annotations

# Локальная база знаний для уточнения OUI
VENDOR_INTELLIGENCE = {
    "4C:63:71": {"vendor": "Xiaomi Communications", "hint": "Mobile / IoT Device"},
    "E0:1F:88": {"vendor": "Xiaomi Communications", "hint": "Mobile / IoT Device"},
    "AC:AF:B9": {"vendor": "Samsung Electronics", "hint": "Mobile Device"},
    "48:27:EA": {"vendor": "Samsung Electronics", "hint": "Mobile Device"},
    "00:1A:79": {"vendor": "Apple, Inc.", "hint": "Likely AirPort / Legacy Apple"},
    "A8:66:7F": {"vendor": "Apple, Inc.", "hint": "Likely iPhone / iPad"},
    "00:11:32": {"vendor": "Apple, Inc.", "hint": "Likely Mac / Apple TV"},
    # Сюда можно добавлять любые известные префиксы
}

def enrich_mac_vendor(mac: str, base_vendor: str) -> dict:
    """
    Возвращает уточненные данные о производителе.
    """
    mac_prefix = mac[:8].upper()
    
    if mac_prefix in VENDOR_INTELLIGENCE:
        intel = VENDOR_INTELLIGENCE[mac_prefix]
        return {
            "vendor": intel["vendor"],
            "vendor_hint": intel["hint"],
            "is_smart": True
        }
    
    return {
        "vendor": base_vendor if base_vendor else "Unknown",
        "vendor_hint": "",
        "is_smart": False
    }
