#!/usr/bin/env python3
"""
SNMP Collector — сбор данных через SNMP v2c.

Архитектура (Generic Collector):
- Только собирает сырые данные (sysDescr, sysObjectID, sysUpTime, sysName, sysServices)
- НЕ интерпретирует данные — это делает Correlation Engine
- Параллельно перебирает community строки (первый успешный — стоп)
- Пропускает SNMP, если устройство не отвечает на ping (SNMP_SKIP_IF_NO_PING)
"""

from __future__ import annotations

import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Fingerprint
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set

# Импорты pysnmp
from pysnmp.hlapi import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    getCmd,
)


# OID для сбора данных
SNMP_OIDS = {
    "sysDescr": Fingerprint.SNMP_OID_SYS_DESCR,
    "sysObjectID": Fingerprint.SNMP_OID_SYS_OBJECT_ID,
    "sysUpTime": Fingerprint.SNMP_OID_SYS_UP_TIME,
    "sysName": Fingerprint.SNMP_OID_SYS_NAME,
    "sysServices": Fingerprint.SNMP_OID_SYS_SERVICES,
}


class SNMPCollector(ActiveCollector):
    """
    Собирает SNMP-данные через v2c.
    НЕ интерпретирует данные — только собирает факты.
    """

    PRIORITY = 45
    RELIABILITY = 85

    def __init__(self):
        super().__init__(timeout=Fingerprint.SNMP_TIMEOUT)
        self.communities = Fingerprint.SNMP_COMMUNITIES
        self.port = Fingerprint.SNMP_PORT
        self.retries = Fingerprint.SNMP_RETRIES
        self.workers = Fingerprint.SNMP_WORKERS
        self.device_timeout = Fingerprint.SNMP_DEVICE_TIMEOUT
        self.skip_if_no_ping = Fingerprint.SNMP_SKIP_IF_NO_PING
        # Переиспользуем SnmpEngine для всех запросов
        self.snmp_engine = SnmpEngine()

    def collect(self, device: Device) -> FingerprintResult:
        """
        Собирает SNMP-данные для одного устройства.
        Параллельно перебирает community строки с общим таймаутом.
        """
        start_time = time.time()

        # Проверка кэша
        cached = cache_get(device.ip, "snmp")
        if cached:
            return FingerprintResult(**cached, source="snmp", elapsed_ms=0.0)

        # Проверка доступности (ping)
        if not self.is_available(device):
            elapsed_ms = (time.time() - start_time) * 1000
            result = FingerprintResult(
                source="snmp",
                raw_data={
                    "responded": False,
                    "reason": "device_unavailable",
                },
                elapsed_ms=elapsed_ms,
            )
            cache_set(device.ip, "snmp", asdict(result))
            return result

        # Проверка ping из context (TTL collector уже собрал эти данные)
        if self.skip_if_no_ping:
            context = getattr(self, "_context", {})
            ttl_result = context.get("ttl", {}).get(device.ip)
            if ttl_result:
                ping_alive = ttl_result.raw_data.get("alive", False)
                if not ping_alive:
                    elapsed_ms = (time.time() - start_time) * 1000
                    result = FingerprintResult(
                        source="snmp",
                        raw_data={
                            "responded": False,
                            "reason": "skipped_no_ping",
                        },
                        elapsed_ms=elapsed_ms,
                    )
                    cache_set(device.ip, "snmp", asdict(result))
                    return result

        # Параллельно перебираем community строки
        result = self._query_device_parallel(device.ip)

        elapsed_ms = (time.time() - start_time) * 1000

        if result is not None:
            fingerprint_result = FingerprintResult(
                source="snmp",
                raw_data=result,
                elapsed_ms=elapsed_ms,
            )
        else:
            fingerprint_result = FingerprintResult(
                source="snmp",
                raw_data={
                    "responded": False,
                    "reason": "no_snmp_response",
                    "communities_tried": self.communities,
                },
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "snmp", asdict(fingerprint_result))

        return fingerprint_result

    def _query_device_parallel(self, ip: str) -> dict | None:
        """
        Параллельно перебирает community строки для одного устройства.
        Возвращает первый успешный результат или None.
        Общий таймаут — SNMP_DEVICE_TIMEOUT.
        """
        with ThreadPoolExecutor(max_workers=len(self.communities)) as executor:
            futures = {
                executor.submit(self._query_single_community, ip, community): community
                for community in self.communities
            }

            try:
                for future in as_completed(futures, timeout=self.device_timeout):
                    community = futures[future]
                    try:
                        result = future.result()
                        if result is not None:
                            return result
                    except Exception:
                        continue
            except TimeoutError:
                pass

        return None

    def _query_single_community(self, ip: str, community: str) -> dict | None:
        """
        Делает SNMP GET для одного устройства с одной community строкой.
        Возвращает dict с сырыми данными или None, если не удалось.
        """
        try:
            oids = [ObjectType(ObjectIdentity(oid)) for oid in SNMP_OIDS.values()]

            # Используем переиспользуемый SnmpEngine
            error_indication, error_status, error_index, var_binds = next(
                getCmd(
                    self.snmp_engine,  # Переиспользуем engine
                    CommunityData(community, mpModel=1),
                    UdpTransportTarget(
                        (ip, self.port),
                        timeout=self.timeout,
                        retries=self.retries,
                    ),
                    ContextData(),
                    *oids,
                )
            )

            if error_indication:
                return None
            if error_status:
                return None

            result = {"responded": True, "community": community}
            oid_to_name = {v: k for k, v in SNMP_OIDS.items()}

            for var_bind in var_binds:
                oid_str = str(var_bind[0])
                value = var_bind[1]

                name = None
                for full_oid, n in oid_to_name.items():
                    if oid_str.startswith(full_oid):
                        name = n
                        break

                if name:
                    if name == "sysServices":
                        result[name] = int(value)
                    elif name == "sysUpTime":
                        result[name] = int(value)
                    else:
                        result[name] = str(value)

            return result

        except Exception:
            return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        """
        Параллельно собирает SNMP-данные для всех устройств.
        """
        if not Fingerprint.SNMP_ENABLED:
            return {}

        self._context = context or {}

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
                    results[ip] = FingerprintResult(source="snmp", elapsed_ms=0.0)

        return results
