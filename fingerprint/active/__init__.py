"""
Активные коллекторы fingerprint.
"""

from .base import ActiveCollector, FingerprintResult
from .ttl import TTLCollector
from .tcp import TCPCollector, CORE_PORTS, OPTIONAL_PORTS, ALL_PORTS
from .http import HTTPCollector, HTTP_PORTS, HTTPS_PORTS
from .ssdp import SSDPCollector
from .snmp import SNMPCollector
from .switch_port import SwitchPortCollector  # <-- ДОБАВЛЕНО
from .ping import ping, PingResult
from .registry import COLLECTORS, get_collectors

__all__ = [
    "ActiveCollector",
    "FingerprintResult",
    "TTLCollector",
    "TCPCollector",
    "HTTPCollector",
    "SSDPCollector",
    "SNMPCollector",
    "SwitchPortCollector",  # <-- ДОБАВЛЕНО
    "CORE_PORTS",
    "OPTIONAL_PORTS",
    "ALL_PORTS",
    "HTTP_PORTS",
    "HTTPS_PORTS",
    "ping",
    "PingResult",
    "COLLECTORS",
    "get_collectors",
]
