#!/usr/bin/env python3
"""
WSD Collector — получение информации через Web Services for Devices (UDP 3702).
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

import socket
import uuid
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


class WSDCollector(ActiveCollector):
    PRIORITY = 48
    RELIABILITY = 85

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.wsd.timeout", 1.5)
        self.workers = self.config.get("collector.wsd.workers", 32)

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

        wsd_data = self._query_wsd(device.ip)
        if wsd_data:
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="WSD",
                device_id=device.ip,
                attribute="wsd_info",
                value=wsd_data
            )]
        return []

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> list:
        """ES-1.8.3: scan теперь возвращает List[Observation] для всех устройств."""
        all_observations = []
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in devices}
            for future in as_completed(futures):
                try:
                    all_observations.extend(future.result())
                except Exception:
                    pass
        return all_observations

    def _query_wsd(self, ip: str) -> dict | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            probe = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsd="http://schemas.xmlsoap.org/ws/2005/04/discovery">
  <soap:Header>
    <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
    <wsa:MessageID>uuid:{str(uuid.uuid4())}</wsa:MessageID>
    <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
  </soap:Header>
  <soap:Body><wsd:Probe/></soap:Body>
</soap:Envelope>"""
            sock.sendto(probe.encode('utf-8'), (ip, 3702))
            data, _ = sock.recvfrom(4096)
            sock.close()
            
            xml_data = data.decode('utf-8', errors='ignore')
            return {
                "responded": True,
                "friendly_name": (m.group(1) if (m := re.search(r'<wsdn:FriendlyName>(.*?)</wsdn:FriendlyName>', xml_data)) else ""),
                "device_type": (m.group(1) if (m := re.search(r'<wsdn:TypeName>(.*?)</wsdn:TypeName>', xml_data)) else ""),
                "manufacturer": (m.group(1) if (m := re.search(r'<wsdn:Manufacturer>(.*?)</wsdn:Manufacturer>', xml_data)) else ""),
                "model": (m.group(1) if (m := re.search(r'<wsdn:ModelName>(.*?)</wsdn:ModelName>', xml_data)) else "")
            }
        except Exception:
            return None
