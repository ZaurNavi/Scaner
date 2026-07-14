"""
Активные коллекторы fingerprint.
"""

from .dhcp_cisco import DHCPCiscoCollector
from .base import ActiveCollector, FingerprintResult
from .scapy_fp import ScapyFPCollector
from .ttl import TTLCollector
from .tcp import TCPCollector, CORE_PORTS, OPTIONAL_PORTS, ALL_PORTS
from .http import HTTPCollector, HTTP_PORTS, HTTPS_PORTS
from .ssdp import SSDPCollector
from .snmp import SNMPCollector
from .switch_port import SwitchPortCollector
from .netbios import NetBIOSCollector
from .wsd import WSDCollector
from .ssh import SSHCollector
from .smb import SMBCollector
from .banners import BannersCollector
from .https_cert import HTTPSCertCollector
from .ntp import NTPCollector             # <-- ДОБАВЛЕНО
from .lldp_cdp import LLDP_CDPCollector   # <-- ДОБАВЛЕНО
from .ping import ping, PingResult
from .registry import COLLECTORS, get_collectors

__all__ = [
    "ActiveCollector",
    "FingerprintResult",
    "ScapyFPCollector",
    "TTLCollector",
    "TCPCollector",
    "HTTPCollector",
    "SSDPCollector",
    "SNMPCollector",
    "SwitchPortCollector",
    "NetBIOSCollector",
    "WSDCollector",
    "SSHCollector",
    "SMBCollector",
    "BannersCollector",
    "HTTPSCertCollector",
    "NTPCollector",        # <-- ДОБАВЛЕНО
    "LLDP_CDPCollector",   # <-- ДОБАВЛЕНО
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
