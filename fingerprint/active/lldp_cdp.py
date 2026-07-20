#!/usr/bin/env python3
"""
LLDP/CDP Collector — обнаружение сетевых устройств через L2-протоколы.
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from scapy.all import Ether, LLC, SNAP, sendp, sniff
from scapy.contrib.cdp import CDPv2_HDR, CDPMsgDeviceID, CDPMsgPortID, CDPMsgCapabilities, CDPMsgPlatform, CDPMsgSoftwareVersion
from scapy.contrib.lldp import LLDPDU, LLDPDUChassisID, LLDPDUPortID, LLDPDUSystemName, LLDPDUSystemDescription

from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


class LLDP_CDPCollector(ActiveCollector):
    PRIORITY = 42
    RELIABILITY = 90

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.lldp_cdp.timeout", 2.0)
        self.workers = self.config.get("collector.lldp_cdp.workers", 16)

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device) or not device.mac:
            return []
        
        dst_mac = device.mac.upper()
        # Пропускаем multicast MAC
        if dst_mac.startswith(("01:00:5E", "33:33", "FF:FF:FF")):
            return []

        lldp_cdp_data = self._probe_device(dst_mac)
        if lldp_cdp_data:
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="LLDP/CDP",
                device_id=device.ip,
                attribute="lldp_cdp_info",
                value=lldp_cdp_data
            )]
        return []

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> list:
        """ES-1.8.3: scan возвращает List[Observation] для всех устройств."""
        # Фильтруем multicast MAC
        targets = [d for d in devices if d.mac and not d.mac.upper().startswith(("01:00:5E", "33:33", "FF:FF:FF"))]
        
        all_observations = []
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                try:
                    all_observations.extend(future.result())
                except Exception:
                    pass
        return all_observations

    def _probe_device(self, dst_mac: str) -> dict | None:
        found_info = {}
        try:
            cdp_pkt = (
                Ether(dst=dst_mac, src="00:00:00:00:00:01") 
                / LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03) 
                / SNAP(OUI=0x00000c, code=0x2000) 
                / CDPv2_HDR(version=2, ttl=180) 
                / CDPMsgDeviceID(val="Scanner") 
                / CDPMsgPortID(iface="eth0")
            )
            lldp_pkt = (
                Ether(dst=dst_mac, src="00:00:00:00:00:01") 
                / LLDPDU() 
                / LLDPDUChassisID(subtype=4, id="00:00:00:00:00:01") 
                / LLDPDUPortID(subtype=3, id="eth0") 
                / LLDPDUSystemName(system_name="Scanner")
            )

            sendp(cdp_pkt, verbose=0)
            sendp(lldp_pkt, verbose=0)

            ans = sniff(
                filter=f"ether src {dst_mac} and (ether proto 0x2000 or ether proto 0x88cc)",
                timeout=self.timeout, 
                count=5
            )

            for pkt in ans:
                if pkt.haslayer(CDPv2_HDR):
                    for msg in pkt[CDPv2_HDR].msg:
                        if isinstance(msg, CDPMsgDeviceID):
                            found_info["cdp_device_id"] = str(msg.val)
                        elif isinstance(msg, CDPMsgPortID):
                            found_info["cdp_port"] = str(msg.iface)
                        elif isinstance(msg, CDPMsgPlatform):
                            found_info["cdp_platform"] = str(msg.val)
                        elif isinstance(msg, CDPMsgSoftwareVersion):
                            found_info["cdp_version"] = str(msg.val)
                elif pkt.haslayer(LLDPDU):
                    if pkt.haslayer(LLDPDUSystemName):
                        found_info["lldp_system_name"] = str(pkt[LLDPDUSystemName].system_name)
                    if pkt.haslayer(LLDPDUSystemDescription):
                        found_info["lldp_description"] = str(pkt[LLDPDUSystemDescription].description)
                    if pkt.haslayer(LLDPDUPortID):
                        found_info["lldp_port"] = str(pkt[LLDPDUPortID].id)

            return {"responded": True, "info": found_info} if found_info else None
        except Exception:
            return None
