#!/usr/bin/env python3
"""
Активные коллекторы fingerprint.
ES-1.8.3: FingerprintResult удалён. Все коллекторы возвращают List[Observation].
"""

from .base import ActiveCollector
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
from .ntp import NTPCollector
from .lldp_cdp import LLDP_CDPCollector
from .dhcp_cisco import DHCPCiscoCollector
from .favicon import FaviconCollector
from .ping import ping, PingResult
from .registry import get_collectors
from .dns_sd import DnsSdCollector

__all__ = [
    "ActiveCollector",
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
    "NTPCollector",
    "LLDP_CDPCollector",
    "DHCPCiscoCollector",
    "FaviconCollector",
    "DnsSdCollector",
    "CORE_PORTS",
    "OPTIONAL_PORTS",
    "ALL_PORTS",
    "HTTP_PORTS",
    "HTTPS_PORTS",
    "ping",
    "PingResult",
    "get_collectors",
]
