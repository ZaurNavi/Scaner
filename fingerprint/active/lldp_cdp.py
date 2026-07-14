#!/usr/bin/env python3
"""
LLDP/CDP Collector — активный запрос информации о сетевом устройстве.
Использует Scapy для отправки CDP/LLDP пакетов на MAC-адрес устройства.
"""

from __future__ import annotations

import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from scapy.all import Ether, LLC, SNAP, sendp, sniff
from scapy.contrib.cdp import CDPMsgDeviceID, CDPMsgPortID, CDPMsgCapabilities, CDPMsgPlatform, CDPMsgVersion, CiscoDiscoveryProtocol
from scapy.contrib.lldp import LLDPDUChassisID, LLDPDUPortID, LLDPDUSystemName, LLDPDUSystemDescription, LLDPDUManagementAddress, LLDPMessage

from config import Fingerprint
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class LLDP_CDPCollector(ActiveCollector):
    PRIORITY = 42  # Высокий приоритет, сразу после базовых проверок
    RELIABILITY = 90

    def __init__(self):
        super().__init__(timeout=2.0)
        self.workers = 16  # Меньше воркеров, т.к. работа с raw-сокетами

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        cached = cache_get(device.ip, "lldp_cdp")
        if cached:
            return FingerprintResult(**cached, source="lldp_cdp", elapsed_ms=0.0)

        if not self.is_available(device) or not device.mac:
            return FingerprintResult(
                source="lldp_cdp",
                raw_data={"responded": False, "reason": "no_mac_or_unavailable"},
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        # Нормализуем MAC для Scapy
        dst_mac = device.mac.upper()
        
        # Если MAC multicast или broadcast, пропускаем (нам нужны конкретные устройства)
        if dst_mac.startswith(("01:00:5E", "33:33", "FF:FF:FF")):
            return FingerprintResult(
                source="lldp_cdp",
                raw_data={"responded": False, "reason": "multicast_mac"},
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        lldp_cdp_data = self._probe_device(dst_mac)
        elapsed_ms = (time.time() - start_time) * 1000

        if lldp_cdp_data:
            result = FingerprintResult(
                source="lldp_cdp",
                raw_data=lldp_cdp_data,
                elapsed_ms=elapsed_ms,
                capabilities=["supports_lldp_cdp"]
            )
        else:
            result = FingerprintResult(
                source="lldp_cdp",
                raw_data={"responded": False, "reason": "no_lldp_cdp_response"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "lldp_cdp", asdict(result))
        return result

    def _probe_device(self, dst_mac: str) -> dict | None:
        """
        Отправляет CDP и LLDP запросы и слушает ответ в течение timeout.
        """
        found_info = {}

        # 1. CDP Probe (Cisco)
        cdp_pkt = Ether(dst=dst_mac, src="00:00:00:00:00:01") / \
                  LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03) / \
                  SNAP(OUI=0x00000c, code=0x2000) / \
                  CiscoDiscoveryProtocol(version=2, ttl=180) / \
                  CDPMsgDeviceID(val="Scanner") / \
                  CDPMsgPortID(iface="eth0")

        # 2. LLDP Probe (Standard)
        lldp_pkt = Ether(dst=dst_mac, src="00:00:00:00:00:01") / \
                   LLDPMessage() / \
                   LLDPDUChassisID(subtype=4, id="00:00:00:00:00:01") / \
                   LLDPDUPortID(subtype=3, id="eth0") / \
                   LLDPDUSystemName(system_name="Scanner")

        try:
            # Отправляем оба пакета
            sendp(cdp_pkt, verbose=0)
            sendp(lldp_pkt, verbose=0)

            # Слушаем ответы в течение timeout
            # Фильтр: пакеты от целевого MAC, содержащие CDP или LLDP
            bpf_filter = f"ether src {dst_mac} and (ether proto 0x2000 or ether proto 0x88cc)"
            ans = sniff(filter=bpf_filter, timeout=self.timeout, count=5)

            for pkt in ans:
                if pkt.haslayer(CiscoDiscoveryProtocol):
                    cdp = pkt[CiscoDiscoveryProtocol]
                    for msg in cdp.msg:
                        if isinstance(msg, CDPMsgDeviceID):
                            found_info["cdp_device_id"] = str(msg.val)
                        elif isinstance(msg, CDPMsgPortID):
                            found_info["cdp_port"] = str(msg.iface)
                        elif isinstance(msg, CDPMsgPlatform):
                            found_info["cdp_platform"] = str(msg.val)
                        elif isinstance(msg, CDPMsgVersion):
                            found_info["cdp_version"] = str(msg.val)
                
                elif pkt.haslayer(LLDPMessage):
                    lldp = pkt[LLDPMessage]
                    for tlv in lldp.tlvs:
                        if isinstance(tlv, LLDPDUSystemName):
                            found_info["lldp_system_name"] = str(tlv.system_name)
                        elif isinstance(tlv, LLDPDUSystemDescription):
                            found_info["lldp_description"] = str(tlv.description)
                        elif isinstance(tlv, LLDPDUPortID):
                            found_info["lldp_port"] = str(tlv.id)

            return {"responded": True, "info": found_info} if found_info else None

        except Exception:
            return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        results: dict[str, FingerprintResult] = {}
        # Сканируем только устройства с известным MAC (локальные)
        targets = [d for d in devices if d.mac and not d.mac.startswith(("01:00:5E", "33:33", "FF:FF:FF"))]
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    results[ip] = future.result()
                except Exception:
                    results[ip] = FingerprintResult(source="lldp_cdp", elapsed_ms=0.0)
        return results
