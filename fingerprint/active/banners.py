#!/usr/bin/env python3
from __future__ import annotations
import socket, time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set
from configuration import ConfigurationManager

class BannersCollector(ActiveCollector):
    PRIORITY = 55
    RELIABILITY = 85
    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.banners.timeout", 1.0)
        self.workers = self.config.get("collector.banners.workers", 64)
        self.ports_to_check = [(21, b"220"), (23, b""), (25, b"220"), (110, b"+OK"), (143, b"* OK"), (554, b"RTSP"), (1883, b""), (3389, b"\x03\x00\x00"), (5900, b"RFB"), (6379, b"-ERR"), (9200, b"\"name\"")]

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()
        cached = cache_get(device.ip, "banners")
        if cached: return FingerprintResult(**cached, source="banners", elapsed_ms=0.0)
        if not self.is_available(device):
            return FingerprintResult(source="banners", raw_data={"responded": False}, elapsed_ms=(time.time() - start_time) * 1000)
        
        banners_data = self._get_banners(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000
        result = FingerprintResult(source="banners", raw_data=banners_data or {"responded": False}, elapsed_ms=elapsed_ms, capabilities=["supports_banners"] if banners_data else [])
        cache_set(device.ip, "banners", asdict(result))
        return result

    def _get_banners(self, ip: str) -> dict | None:
        found_banners = {}
        for port, expected_prefix in self.ports_to_check:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                sock.connect((ip, port))
                if port == 1883: sock.send(b"\x10\x16\x00\x04MQTT\x04\x02\x00\x3c\x00\x0bScannerTest")
                elif port == 9200: sock.send(b"GET / HTTP/1.0\r\n\r\n")
                elif port == 3389: sock.send(b"\x03\x00\x00\x13\x0e\xe0\x00\x00\x00\x00\x00\x01\x00\x08\x00\x03\x00\x00\x00")
                response = sock.recv(512)
                sock.close()
                if response:
                    banner_str = response.decode('utf-8', errors='ignore').strip().replace('\r', '').replace('\n', ' ')
                    if not expected_prefix or banner_str.encode('utf-8', errors='ignore').startswith(expected_prefix):
                        found_banners[str(port)] = banner_str[:150]
            except Exception: continue
        return {"responded": True, "banners": found_banners} if found_banners else None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        targets = devices
        if context and "tcp" in context:
            tcp_ctx = context["tcp"]
            target_ports = {21, 23, 25, 110, 143, 554, 1883, 3389, 5900, 6379, 9200}
            targets = [d for d in devices if tcp_ctx.get(d.ip) and any(str(p) in tcp_ctx[d.ip].raw_data.get("open_ports", []) or int(p) in tcp_ctx[d.ip].raw_data.get("open_ports", []) for p in target_ports)]
        results = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                ip = futures[future]
                try: results[ip] = future.result()
                except Exception: results[ip] = FingerprintResult(source="banners", elapsed_ms=0.0)
        return results
