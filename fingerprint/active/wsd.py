#!/usr/bin/env python3
"""
WSD Collector — получение информации через Web Services for Devices (UDP 3702).
Отлично находит Windows-ПК, сетевые принтеры и МФУ.
"""

from __future__ import annotations

import socket
import uuid
import time
import re
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Fingerprint
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class WSDCollector(ActiveCollector):
    PRIORITY = 48
    RELIABILITY = 85

    def __init__(self):
        super().__init__(timeout=1.5)
        self.workers = 32

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        cached = cache_get(device.ip, "wsd")
        if cached:
            return FingerprintResult(**cached, source="wsd", elapsed_ms=0.0)

        if not self.is_available(device):
            elapsed_ms = (time.time() - start_time) * 1000
            return FingerprintResult(
                source="wsd",
                raw_data={"responded": False, "reason": "device_unavailable"},
                elapsed_ms=elapsed_ms,
            )

        wsd_data = self._query_wsd(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if wsd_data:
            result = FingerprintResult(source="wsd", raw_data=wsd_data, elapsed_ms=elapsed_ms)
        else:
            result = FingerprintResult(
                source="wsd",
                raw_data={"responded": False, "reason": "no_wsd_response"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "wsd", asdict(result))
        return result

    def _query_wsd(self, ip: str) -> dict | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)

            msg_id = str(uuid.uuid4())
            probe = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsd="http://schemas.xmlsoap.org/ws/2005/04/discovery">
  <soap:Header>
    <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
    <wsa:MessageID>uuid:{msg_id}</wsa:MessageID>
    <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
  </soap:Header>
  <soap:Body>
    <wsd:Probe/>
  </soap:Body>
</soap:Envelope>"""

            sock.sendto(probe.encode('utf-8'), (ip, 3702))
            data, _ = sock.recvfrom(4096)
            sock.close()

            xml_data = data.decode('utf-8', errors='ignore')
            
            # Парсим FriendlyName и DeviceType
            friendly_name = re.search(r'<wsdn:FriendlyName>(.*?)</wsdn:FriendlyName>', xml_data)
            device_type = re.search(r'<wsdn:TypeName>(.*?)</wsdn:TypeName>', xml_data)
            manufacturer = re.search(r'<wsdn:Manufacturer>(.*?)</wsdn:Manufacturer>', xml_data)
            model = re.search(r'<wsdn:ModelName>(.*?)</wsdn:ModelName>', xml_data)

            return {
                "responded": True,
                "friendly_name": friendly_name.group(1) if friendly_name else "",
                "device_type": device_type.group(1) if device_type else "",
                "manufacturer": manufacturer.group(1) if manufacturer else "",
                "model": model.group(1) if model else "",
            }

        except (socket.timeout, socket.error):
            return None
        except Exception:
            return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        results: dict[str, FingerprintResult] = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, device): device.ip for device in devices}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    results[ip] = future.result()
                except Exception:
                    results[ip] = FingerprintResult(source="wsd", elapsed_ms=0.0)
        return results
