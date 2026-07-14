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
from .netbios import NetBIOSCollector  # <-- ДОБАВЛЕНО


# Единый реестр всех активных коллекторов
# Порядок важен:
# 1. TTL — базовая проверка доступности (priority 40)
# 2. SNMP — сбор sysDescr и т.д. (priority 45)
# 3. Switch Port — определение порта коммутатора (priority 46)
# 4. NetBIOS — получение имени Windows (priority 47)
# 5. TCP — сканирование портов (priority 50)
# 6. SSDP — multicast (priority 60)
# 7. HTTP — использует результат TCP (priority 70)
COLLECTORS: list[ActiveCollector] = [
    TTLCollector(),
    SNMPCollector(),
    SwitchPortCollector(),
    NetBIOSCollector(),  # <-- ДОБАВЛЕНО
    TCPCollector(),
    SSDPCollector(),
    HTTPCollector(),
]


def get_collectors() -> list[ActiveCollector]:
    """
    Возвращает список всех зарегистрированных коллекторов.
    """
    return COLLECTORS
