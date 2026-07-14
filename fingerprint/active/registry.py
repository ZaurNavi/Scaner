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
from .banners import BannersCollector
from .https_cert import HTTPSCertCollector
from .ntp import NTPCollector             # <-- ДОБАВЛЕНО
from .lldp_cdp import LLDP_CDPCollector   # <-- ДОБАВЛЕНО


COLLECTORS: list[ActiveCollector] = [
    ScapyFPCollector(),
    TTLCollector(),
    LLDP_CDPCollector(),    # <-- ДОБАВЛЕНО (высокий приоритет для сетевых устройств)
    SNMPCollector(),
    SwitchPortCollector(),
    NetBIOSCollector(),
    WSDCollector(),
    SSHCollector(),
    SMBCollector(),
    BannersCollector(),
    NTPCollector(),         # <-- ДОБАВЛЕНО
    TCPCollector(),
    SSDPCollector(),
    HTTPCollector(),
    HTTPSCertCollector(),
]


def get_collectors() -> list[ActiveCollector]:
    return COLLECTORS
