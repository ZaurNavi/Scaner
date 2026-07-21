#!/usr/bin/env python3
"""
Vendor heuristics — эвристики определения производителя устройства.
ES-1.8.4: Предметные знания, не связанные с отчётами.
"""

from .heuristics import guess_vendor_from_name, VENDOR_KEYWORDS

__all__ = [
    "guess_vendor_from_name",
    "VENDOR_KEYWORDS",
]
