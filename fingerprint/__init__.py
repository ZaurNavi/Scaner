"""
Repeater Monitor
fingerprint/

Определение характеристик устройства по доступным данным.

Архитектура:
1. Collection — сбор данных из всех источников (один раз для всей сети)
2. Analysis — применение эвристик к каждому устройству
"""

from .analysis import fingerprint_all

__all__ = ["fingerprint_all"]
