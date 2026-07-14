#!/usr/bin/env python3
"""
Реестр коллекторов.
"""

from __future__ import annotations

from .scapy_fp import ScapyFPCollector  # <-- ДОБАВЛЕНО
from .base import ActiveCollector
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
from .https_cert import HTTPSCertCollector  # <-- ДОБАВЛЕНО


# Единый реестр всех активных коллекторов
COLLECTORS: list[ActiveCollector] = [
    ScapyFPCollector(),
    TTLCollector(),
    SNMPCollector(),
    SwitchPortCollector(),
    NetBIOSCollector(),
    WSDCollector(),
    SSHCollector(),
    SMBCollector(),
    TCPCollector(),
    SSDPCollector(),
    HTTPCollector(),
    HTTPSCertCollector(),  # <-- ДОБАВЛЕНО (после HTTP, т.к. использует TCP context)
]


def get_collectors() -> list[ActiveCollector]:
    return COLLECTORS
