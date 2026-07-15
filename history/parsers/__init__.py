#!/usr/bin/env python3
"""
Парсеры для специфичных контроллеров.
Эти парсеры используются движками (Mobility Engine и т.д.), а не History Service.
"""

from .omada import OmadaParser

__all__ = ["OmadaParser"]
