#!/usr/bin/env python3
"""
Traffic Collector Module.
"""

from .collector import TrafficCollector, traffic_collector
from .models import TrafficInfo

__all__ = [
    "TrafficCollector",
    "traffic_collector",
    "TrafficInfo",
]
