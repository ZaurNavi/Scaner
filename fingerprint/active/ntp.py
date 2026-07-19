#!/usr/bin/env python3
from __future__ import annotations
import socket, struct, time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set
from configuration import ConfigurationManager

class NTPCollector(ActiveCollector):
    PRIORITY = 58
    RELIABILITY = 75
    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.ntp.timeout", 1.0)
        self.workers = self.config.get("collector.ntp.workers", 32)
        self.port = self.config.get("collector.ntp.port", 123)

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()
        cached = cache_get(device.ip, "ntp")
        if cached: return FingerprintResult(**cached, source="ntp", elapsed_ms=0.0)
        if not self.is_available(device):
            return FingerprintResult(source="ntp", raw_data={"responded": False, "reason": "device_unavailable"}, elapsed_ms=(time.time() - start_time) * 1000)
        
        ntp_data = self._query_ntp(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000
        result = FingerprintResult(source="ntp", raw_data=ntp_data or {"responded": False, "reason": "no_ntp_response"}, elapsed_ms=elapsed_ms, capabilities=["supports_ntp"] if ntp_data else [])
        cache_set(device.ip, "ntp", asdict(result))
        return result

    def _query_ntp(self, ip: str) -> dict | None:
        try:
            packet = b'\x1b' + 47 * b'\0'
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            sock.sendto(packet, (ip, self.port))
            data, _ = sock.recvfrom(256)
            sock.close()
            if len(data) >= 48:
                t = struct.unpack("!12I", data[:48])
                stratum = t[1] >> 24 & 0xFF
                ref_id = data[12:16]
                try: ref_id_str = ref_id.decode('ascii', errors='ignore').strip()
                except: ref_id_str = ref_id.hex()
                return {"responded": True, "stratum": stratum, "reference_id": ref_id_str, "poll_interval": t[2] >> 24 & 0xFF, "precision": t[3] >> 24 & 0xFF if (t[3] >> 24 & 0x80) else t[3] >> 24}
            return None
        except Exception: return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        results = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in devices}
            for future in as_completed(futures):
                ip = futures[future]
                try: results[ip] = future.result()
                except Exception: results[ip] = FingerprintResult(source="ntp", elapsed_ms=0.0)
        return results
