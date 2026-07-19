#!/usr/bin/env python3
from __future__ import annotations
import socket, time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set
from configuration import ConfigurationManager

class SMBCollector(ActiveCollector):
    PRIORITY = 52
    RELIABILITY = 85
    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.smb.timeout", 1.0)
        self.workers = self.config.get("collector.smb.workers", 64)
        self.port = self.config.get("collector.smb.port", 445)
        self.smb2_probe = bytes.fromhex("00000048fef5424d400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000......") # Сокращено для краткости, используй оригинальный hex из твоего файла

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()
        cached = cache_get(device.ip, "smb")
        if cached: return FingerprintResult(**cached, source="smb", elapsed_ms=0.0)
        if not self.is_available(device):
            return FingerprintResult(source="smb", raw_data={"responded": False, "reason": "device_unavailable"}, elapsed_ms=(time.time() - start_time) * 1000)
        
        smb_data = self._get_smb_info(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000
        result = FingerprintResult(source="smb", raw_data=smb_data or {"responded": False, "reason": "no_smb_response"}, elapsed_ms=elapsed_ms)
        cache_set(device.ip, "smb", asdict(result))
        return result

    def _get_smb_info(self, ip: str) -> dict | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, self.port))
            sock.send(self.smb2_probe)
            response = sock.recv(256)
            sock.close()
            if len(response) >= 64 and response[4:8] == b'\xfe\x53\x4d\x42':
                return {"responded": True, "protocol": "SMB2/3", "os_version": "Windows/Samba (SMB2+)"}
            elif len(response) > 0:
                return {"responded": True, "protocol": "SMB1/Unknown", "raw_hex": response[:32].hex()}
            return None
        except Exception: return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        results = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in devices}
            for future in as_completed(futures):
                ip = futures[future]
                try: results[ip] = future.result()
                except Exception: results[ip] = FingerprintResult(source="smb", elapsed_ms=0.0)
        return results
