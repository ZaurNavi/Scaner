#!/usr/bin/env python3
"""
Реестр коллекторов.
v1.7.1: Внедрение Dependency Injection через ConfigurationManager.
"""

from __future__ import annotations

from typing import List
from configuration import ConfigurationManager

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
from .ntp import NTPCollector
from .lldp_cdp import LLDP_CDPCollector
from .dhcp_cisco import DHCPCiscoCollector
from .favicon import FaviconCollector
from .dns_sd import DnsSdCollector


def get_collectors(configuration: ConfigurationManager) -> List[ActiveCollector]:
    """
    Создает и возвращает список всех активных коллекторов с внедренной конфигурацией.
    """
    return [
        DHCPCiscoCollector(configuration),
        ScapyFPCollector(configuration),
        TTLCollector(configuration),
        LLDP_CDPCollector(configuration),
        SNMPCollector(configuration),
        SwitchPortCollector(configuration),
        NetBIOSCollector(configuration),
        WSDCollector(configuration),
        SSHCollector(configuration),
        SMBCollector(configuration),
        BannersCollector(configuration),
        NTPCollector(configuration),
        TCPCollector(configuration),
        SSDPCollector(configuration),
        HTTPCollector(configuration),
        HTTPSCertCollector(configuration),
        FaviconCollector(configuration),
        DnsSdCollector(configuration),
    ]
