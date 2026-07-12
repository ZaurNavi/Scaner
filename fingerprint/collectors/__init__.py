"""
Коллекторы данных из различных источников.
"""

from .dns import collect_hostnames
from .mdns import collect_mdns, MDNSInfo
from .base import collect_all, CollectedData

__all__ = [
    "collect_all",
    "collect_hostnames",
    "collect_mdns",
    "CollectedData",
    "MDNSInfo",
]
