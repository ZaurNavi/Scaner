#!/usr/bin/env python3
"""
Identity — подсистема идентификации устройств.
ES-1.8.4: Содержит эвристики определения характеристик по наблюдениям.
"""

from .vendor import guess_vendor_from_name, VENDOR_KEYWORDS

__all__ = [
    "guess_vendor_from_name",
    "VENDOR_KEYWORDS",
]
