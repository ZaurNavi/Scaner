#!/usr/bin/env python3
"""
Реестр источников трафика.
"""

from __future__ import annotations

from typing import List, Type
from .sources.base import TrafficSource
from .sources.netflow import NetFlowSource
from .sources.omada import OmadaTrafficSource

_registered_sources: List[TrafficSource] = []


def register_traffic_source(source_class: Type[TrafficSource]) -> None:
    """(Пункт 6) Регистрация класса источника."""
    instance = source_class()
    if instance.is_available():
        _registered_sources.append(instance)
        # Сортируем по приоритету (Пункт 10)
        _registered_sources.sort(key=lambda x: x.priority)


# Регистрация источников по умолчанию
register_traffic_source(NetFlowSource)
register_traffic_source(OmadaTrafficSource)


def get_traffic_sources() -> List[TrafficSource]:
    return _registered_sources
