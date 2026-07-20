#!/usr/bin/env python3
"""
Normalization Rules — правила преобразования Observation.
ES-1.8.1: Автоматическая регистрация через декоратор.
"""

# Импорты запускают декораторы @normalization_rule
from . import dns
from . import mdns

__all__ = ["dns", "mdns"]
