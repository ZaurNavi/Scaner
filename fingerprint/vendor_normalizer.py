#!/usr/bin/env python3
"""
MAC Vendor Normalizer — стандартизация имён производителей для улучшения аналитики.
"""

from __future__ import annotations

# Словарь нормализации: ключевые слова -> каноническое имя
VENDOR_ALIASES = {
    "samsung electronics co.,ltd": "Samsung",
    "samsung electronics": "Samsung",
    "samsung mobile": "Samsung",
    "samsung": "Samsung",
    
    "cisco systems": "Cisco",
    "cisco-linksys": "Cisco",
    "cisco": "Cisco",
    
    "xiaomi communications": "Xiaomi",
    "xiaomi": "Xiaomi",
    
    "tp-link technologies": "TP-Link",
    "tp-link": "TP-Link",
    
    "apple, inc.": "Apple",
    "apple": "Apple",
    
    "microsoft corporation": "Microsoft",
    "microsoft": "Microsoft",
    
    "intel corporate": "Intel",
    "intel": "Intel",
    
    "ubiquiti inc.": "Ubiquiti",
    "ubiquiti": "Ubiquiti",
    
    "mikrotik": "MikroTik",
}

def normalize_vendor(vendor: str) -> str:
    """
    Приводит имя вендора к каноническому виду.
    """
    if not vendor or vendor.strip().lower() in ("unknown", "n/a", ""):
        return "Unknown"
    
    v_lower = vendor.lower().strip()
    
    # Ищем совпадение по ключевым словам
    for keyword, canonical_name in VENDOR_ALIASES.items():
        if keyword in v_lower:
            return canonical_name
            
    # Если не нашли, возвращаем исходное значение, но с правильным регистром (Title Case)
    return vendor.title()
