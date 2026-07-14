#!/usr/bin/env python3
"""
Switch Port Collector — определение порта коммутатора по MAC-адресу.

Использует Bridge MIB для поиска порта:
1. MAC → Bridge Port (dot1dTpFdbPort)
2. Bridge Port → ifIndex (dot1dBasePortIfIndex)
3. ifIndex → Interface Name (ifDescr или ifName)
"""

from __future__ import annotations

import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Cisco, Fingerprint
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set

from pysnmp.hlapi import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    nextCmd,
    getCmd,
)


class SwitchPortCollector(ActiveCollector):
    """
    Определяет порт коммутатора, к которому подключено устройство.
    """

    PRIORITY = 46  # Сразу после SNMP
    RELIABILITY = 90

    def __init__(self):
        super().__init__(timeout=Fingerprint.SNMP_TIMEOUT)
        self.communities = Fingerprint.SNMP_COMMUNITIES
        self.port = Fingerprint.SNMP_PORT
        self.retries = Fingerprint.SNMP_RETRIES
        self.workers = Fingerprint.SNMP_WORKERS
        self.snmp_engine = SnmpEngine()

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        # Проверка кэша
        cached = cache_get(device.ip, "switch_port")
        if cached:
            return FingerprintResult(**cached, source="switch_port", elapsed_ms=0.0)

        if not device.mac:
            elapsed_ms = (time.time() - start_time) * 1000
            result = FingerprintResult(
                source="switch_port",
                raw_data={"responded": False, "reason": "no_mac_address"},
                elapsed_ms=elapsed_ms,
            )
            return result

        # Нормализуем MAC для SNMP (убираем двоеточия, приводим к нижнему регистру)
        mac_normalized = device.mac.replace(":", "").lower()

        # Ищем порт на коммутаторе
        port_info = self._find_port_on_switch(mac_normalized)
        elapsed_ms = (time.time() - start_time) * 1000

        if port_info:
            fingerprint_result = FingerprintResult(
                source="switch_port",
                raw_data=port_info,
                elapsed_ms=elapsed_ms,
            )
        else:
            fingerprint_result = FingerprintResult(
                source="switch_port",
                raw_data={"responded": False, "reason": "port_not_found"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "switch_port", asdict(fingerprint_result))
        return fingerprint_result

    def _find_port_on_switch(self, mac: str) -> dict | None:
        """
        Ищет порт коммутатора по MAC-адресу.
        """
        switch_ip = Cisco.IP

        for community in self.communities:
            try:
                # Шаг 1: MAC → Bridge Port
                bridge_port = self._get_bridge_port(switch_ip, community, mac)
                if bridge_port is None:
                    continue

                # Шаг 2: Bridge Port → ifIndex
                if_index = self._get_if_index(switch_ip, community, bridge_port)
                if if_index is None:
                    continue

                # Шаг 3: ifIndex → Interface Name
                interface_name = self._get_interface_name(switch_ip, community, if_index)
                if interface_name is None:
                    interface_name = f"ifIndex-{if_index}"

                return {
                    "responded": True,
                    "switch_ip": switch_ip,
                    "mac": mac,
                    "bridge_port": bridge_port,
                    "if_index": if_index,
                    "interface_name": interface_name,
                    "community": community,
                }

            except Exception:
                continue

        return None

    def _get_bridge_port(self, switch_ip: str, community: str, mac: str) -> int | None:
        """
        dot1dTpFdbPort: MAC → Bridge Port
        OID: 1.3.6.1.2.1.17.4.3.1.2.{mac}
        """
        mac_oid = ".".join(str(int(x, 16)) for x in [mac[i:i+2] for i in range(0, 12, 2)])
        oid = f"1.3.6.1.2.1.17.4.3.1.2.{mac_oid}"

        try:
            error_indication, error_status, error_index, var_binds = next(
                getCmd(
                    self.snmp_engine,
                    CommunityData(community, mpModel=1),
                    UdpTransportTarget((switch_ip, self.port), timeout=self.timeout, retries=self.retries),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )
            )

            if error_indication or error_status:
                return None

            for var_bind in var_binds:
                return int(var_bind[1])

        except Exception:
            return None

    def _get_if_index(self, switch_ip: str, community: str, bridge_port: int) -> int | None:
        """
        dot1dBasePortIfIndex: Bridge Port → ifIndex
        OID: 1.3.6.1.2.1.17.1.4.1.2.{bridge_port}
        """
        oid = f"1.3.6.1.2.1.17.1.4.1.2.{bridge_port}"

        try:
            error_indication, error_status, error_index, var_binds = next(
                getCmd(
                    self.snmp_engine,
                    CommunityData(community, mpModel=1),
                    UdpTransportTarget((switch_ip, self.port), timeout=self.timeout, retries=self.retries),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )
            )

            if error_indication or error_status:
                return None

            for var_bind in var_binds:
                return int(var_bind[1])

        except Exception:
            return None

    def _get_interface_name(self, switch_ip: str, community: str, if_index: int) -> str | None:
        """
        ifDescr: ifIndex → Interface Name
        OID: 1.3.6.1.2.1.2.2.1.2.{if_index}
        """
        oid = f"1.3.6.1.2.1.2.2.1.2.{if_index}"

        try:
            error_indication, error_status, error_index, var_binds = next(
                getCmd(
                    self.snmp_engine,
                    CommunityData(community, mpModel=1),
                    UdpTransportTarget((switch_ip, self.port), timeout=self.timeout, retries=self.retries),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )
            )

            if error_indication or error_status:
                return None

            for var_bind in var_binds:
                return str(var_bind[1])

        except Exception:
            return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        """
        Параллельно собирает информацию о портах для всех устройств.
        """
        results: dict[str, FingerprintResult] = {}

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {
                executor.submit(self.collect, device): device.ip
                for device in devices
            }

            for future in as_completed(futures):
                ip = futures[future]
                try:
                    result = future.result()
                    results[ip] = result
                except Exception:
                    results[ip] = FingerprintResult(source="switch_port", elapsed_ms=0.0)

        return results
