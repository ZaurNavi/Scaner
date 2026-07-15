#!/usr/bin/env python3
"""
Категории фактов для Confidence Service.
Все категории оформлены через Enum.
"""

from enum import Enum


class FactCategory(Enum):
    """Категории оцениваемых фактов."""
    VENDOR = "vendor"
    MODEL = "model"
    HOSTNAME = "hostname"
    OS = "os"
    DEVICE_TYPE = "device_type"
    MANUFACTURER = "manufacturer"
    WIRELESS_TYPE = "wireless_type"
    CONNECTION = "connection"
    SSID = "ssid"
    ACCESS_POINT = "access_point"
    VLAN = "vlan"
    RADIO = "radio"
    WIFI_CAPABILITY = "wifi_capability"
