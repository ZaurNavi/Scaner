#!/usr/bin/env python3
"""
Перечень источников данных (Source of Truth).
"""

from enum import Enum


class Source(str, Enum):
    """Источники данных для Observation."""
    ARP = "ARP"
    DNS = "DNS"
    MDNS = "MDNS"
    TTL = "TTL"
    TCP = "TCP"
    HTTP = "HTTP"
    SSDP = "SSDP"
    SNMP = "SNMP"
    OUI = "OUI"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"
