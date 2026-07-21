#!/usr/bin/env python3
"""
Vendor Heuristics — эвристики определения производителя по имени устройства.
ES-1.8.4: Предметные знания, не связанные с отчётами.
"""

from __future__ import annotations


# ---------------------------------------------------------
# Словарь vendor → keywords для эвристики по hostname/model
# ---------------------------------------------------------

VENDOR_KEYWORDS: dict[str, list[str]] = {
    "Samsung": [
        "galaxy", "samsung",
        # Galaxy A-серия
        "a01", "a02", "a03", "a04", "a05",
        "a10", "a11", "a12", "a13", "a14", "a15", "a16",
        "a20", "a21", "a22", "a23", "a24", "a25", "a26",
        "a30", "a31", "a32", "a33", "a34", "a35", "a36",
        "a40", "a41", "a42", "a50", "a51", "a52", "a53", "a54", "a55", "a56",
        "a70", "a71", "a72", "a73",
        # Galaxy S-серия
        "s20", "s21", "s22", "s23", "s24", "s25",
        # Galaxy Note
        "note8", "note9", "note10", "note20",
        # Galaxy M-серия
        "m30", "m31", "m32", "m51", "m52",
    ],
    "Xiaomi": [
        "xiaomi", "redmi", "poco", "mi ", "mi-", "mi_",
        "redmi note", "redminote",
        "mi 9", "mi 10", "mi 11",
        "poco x3", "poco x4", "poco x5", "poco f3", "poco f4", "poco f5",
    ],
    "Apple": [
        "apple", "iphone", "ipad", "macbook", "imac", "ipod",
    ],
    "Honor/Huawei": [
        "honor", "huawei",
        # Huawei Y/P/Mate серии
        "y5p", "y6p", "y7p", "y9p",
        "p20", "p30", "p40", "p50",
        "mate20", "mate30", "mate40", "mate50",
        "nova 3", "nova 5", "nova 7", "nova 9",
    ],
    "Lenovo": [
        "lenovo", "thinkpad", "ideapad", "yoga",
    ],
    "OPPO/Realme": [
        "oppo", "realme", "oneplus",
    ],
    "Google": [
        "pixel",
    ],
    "Sony": [
        "sony", "xperia",
    ],
    "Nokia": [
        "nokia",
    ],
    "Asus": [
        "asus", "zenfone", "rog phone",
    ],
}


def guess_vendor_from_name(name: str) -> str | None:
    """
    Пытается определить vendor по строке (hostname или model).
    Использует словарь VENDOR_KEYWORDS.
    
    Returns:
        Название vendor или None, если не удалось определить.
    """
    if not name:
        return None
    name_lower = name.lower()
    for vendor, keywords in VENDOR_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                return vendor
    return None
