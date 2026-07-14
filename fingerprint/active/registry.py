#!/usr/bin/env python3
"""
Реестр коллекторов.
"""

from __future__ import annotations

from .base import ActiveCollector
from .ttl import TTLCollector
from .tcp import TCPCollector
from .ssdp import SSDPCollector
from .snmp import SNMPCollector
from .http import HTTPCollector
from .switch_port import SwitchPortCollector
from .netbios import NetBIOSCollector
from .wsd import WSDCollector          # <-- ДОБАВЛЕНО
from .ssh import SSHCollector          # <-- ДОБАВЛЕНО
from .smb import SMBCollector          # <-- ДОБАВЛЕНО


# Единый реестр всех активных коллекторов
COLLECTORS: list[ActiveCollector] = [
    TTLCollector(),
    SNMPCollector(),
    SwitchPortCollector(),
    NetBIOSCollector(),
    WSDCollector(),       # <-- ДОБАВЛЕНО
    SSHCollector(),       # <-- ДОБАВЛЕНО
    SMBCollector(),       # <-- ДОБАВЛЕНО
    TCPCollector(),
    SSDPCollector(),
    HTTPCollector(),
]


def get_collectors() -> list[ActiveCollector]:
    return COLLECTORS
