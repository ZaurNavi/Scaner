#!/usr/bin/env python3
"""
Реестр коллекторов.
"""

from __future__ import annotations

from .base import ActiveCollector
from .scapy_fp import ScapyFPCollector
from .ttl import TTLCollector
from .tcp import TCPCollector
from .ssdp import SSDPCollector
from .snmp import SNMPCollector
from .http import HTTPCollector
from .switch_port import SwitchPortCollector
from .netbios import NetBIOSCollector
from .wsd import WSDCollector
from .ssh import SSHCollector
from .smb import SMBCollector
from .https_cert import HTTPSCertCollector
from .banners import BannersCollector  # <-- ДОБАВЛЕНО


COLLECTORS: list[ActiveCollector] = [
    ScapyFPCollector(),
    TTLCollector(),
    SNMPCollector(),
    SwitchPortCollector(),
    NetBIOSCollector(),
    WSDCollector(),
    SSHCollector(),
    SMBCollector(),
    BannersCollector(),    # <-- ДОБАВЛЕНО (проверяет FTP, Telnet, RTSP, SIP)
    TCPCollector(),
    SSDPCollector(),
    HTTPCollector(),
    HTTPSCertCollector(),
]


def get_collectors() -> list[ActiveCollector]:
    return COLLECTORS
