#!/usr/bin/env python3
"""
SNMP Collector — сбор данных через SNMP v2c.
v1.7.1: Интеграция с Configuration Layer.
"""

from __future__ import annotations

import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set
from configuration import ConfigurationManager

from pysnmp.hlapi import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, getCmd,
)


class SNMPCollector(ActiveCollector):
    PRIORITY = 45
    RELIABILITY = 85

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.communities = [c.strip() for c in self.config.get("collector.snmp.communities", "public").split(",")]
        self.port = self.config.get("collector.snmp.port", 161)
        self.retries = self.config.get("collector.snmp.retries", 2)
        self.workers = self.config.get("collector.snmp.workers", 16)
        self.device_timeout = self.config.get("collector.snmp.device_timeout", 5.0)
        self.skip_if_no_ping = self.config.get("collector.snmp.skip_if_no_ping", True)
        self.timeout = self.config.get("collector.snmp.timeout", 2.0)
        
        self.oids = {
            "sysDescr": self.config.get("collector.snmp.oid.sys_descr", "1.3.6.1.2.1.1.1.0"),
            "sysObjectID": self.config.get("collector.snmp.oid.sys_object_id", "1.3.6.1.2.1.1.2.0"),
            "sysUpTime": self.config.get("collector.snmp.oid.sys_up_time", "1.3.6.1.2.1.1.3.0"),
            "sysName": self.config.get("collector.snmp.oid.sys_name", "1.3.6.1.2.1.1.5.0"),
            "sysServices": self.config.get("collector.snmp.oid.sys_services", "1.3.6.1.2.1.1.7.0"),
            "sysLocation": self.config.get("collector.snmp.oid.sys_location", "1.3.6.1.2.1.1.6.0"),
            "sysContact": self.config.get("collector.snmp.oid.sys_contact", "1.3.6.1.2.1.1.4.0"),
        }
        self.snmp_engine = SnmpEngine()

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()
        cached = cache_get(device.ip, "snmp")
        if cached:
            return FingerprintResult(**cached, source="snmp", elapsed_ms=0.0)

        if not self.is_available(device):
            result = FingerprintResult(source="snmp", raw_data={"responded": False, "reason": "device_unavailable"}, elapsed_ms=(time.time() - start_time) * 1000)
            cache_set(device.ip, "snmp", asdict(result))
            return result

        if self.skip_if_no_ping:
            context = getattr(self, "_context", {})
            ttl_result = context.get("ttl", {}).get(device.ip)
            if ttl_result and not ttl_result.raw_data.get("alive", False):
                result = FingerprintResult(source="snmp", raw_data={"responded": False, "reason": "skipped_no_ping"}, elapsed_ms=(time.time() - start_time) * 1000)
                cache_set(device.ip, "snmp", asdict(result))
                return result

        result = self._query_device_parallel(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if result is not None:
            fingerprint_result = FingerprintResult(source="snmp", raw_data=result, elapsed_ms=elapsed_ms)
        else:
            fingerprint_result = FingerprintResult(
                source="snmp",
                raw_data={"responded": False, "reason": "no_snmp_response", "communities_tried": self.communities},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "snmp", asdict(fingerprint_result))
        return fingerprint_result

    def _query_device_parallel(self, ip: str) -> dict | None:
        with ThreadPoolExecutor(max_workers=len(self.communities)) as executor:
            futures = {executor.submit(self._query_single_community, ip, community): community for community in self.communities}
            try:
                for future in as_completed(futures, timeout=self.device_timeout):
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
        try:
            oids = [ObjectType(ObjectIdentity(oid)) for oid in self.oids.values()]
            error_indication, error_status, error_index, var_binds = next(
                getCmd(
                    self.snmp_engine,
                    CommunityData(community, mpModel=1),
                    UdpTransportTarget((ip, self.port), timeout=self.timeout, retries=self.retries),
                    ContextData(),
                    *oids,
                )
            )
            if error_indication or error_status:
                return None

            result = {"responded": True, "community": community}
            oid_to_name = {v: k for k, v in self.oids.items()}

            for var_bind in var_binds:
                oid_str = str(var_bind[0])
                value = var_bind[1]
                name = next((n for full_oid, n in oid_to_name.items() if oid_str.startswith(full_oid)), None)
                if name:
                    result[name] = int(value) if name in ("sysServices", "sysUpTime") else str(value)
            return result
        except Exception:
            return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        if not self.config.get("collector.snmp.enabled", True):
            return {}
        self._context = context or {}
        return super().scan(devices, context=context, **kwargs)
