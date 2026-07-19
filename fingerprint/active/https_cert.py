#!/usr/bin/env python3
from __future__ import annotations
import socket, ssl, time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set
from configuration import ConfigurationManager

class HTTPSCertCollector(ActiveCollector):
    PRIORITY = 75
    RELIABILITY = 90
    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.https_cert.timeout", 2.0)
        self.workers = self.config.get("collector.https_cert.workers", 32)
        ports_str = self.config.get("collector.https_cert.ports", "443,8443,4443")
        self.ports = [int(p) for p in ports_str.split(",")]

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()
        cached = cache_get(device.ip, "https_cert")
        if cached: return FingerprintResult(**cached, source="https_cert", elapsed_ms=0.0)
        if not self.is_available(device):
            return FingerprintResult(source="https_cert", raw_data={"responded": False, "reason": "device_unavailable"}, elapsed_ms=(time.time() - start_time) * 1000)
        
        tls_data = self._get_tls_fingerprint(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000
        result = FingerprintResult(source="https_cert", raw_data=tls_data or {"responded": False, "reason": "no_https_or_timeout"}, elapsed_ms=elapsed_ms, capabilities=["supports_https", "supports_tls_fp"] if tls_data else [])
        cache_set(device.ip, "https_cert", asdict(result))
        return result

    def _get_tls_fingerprint(self, ip: str) -> dict | None:
        for port in self.ports:
            try:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                with context.wrap_socket(sock, server_hostname=ip) as ssock:
                    ssock.connect((ip, port))
                    cert = ssock.getpeercert()
                    tls_version = ssock.version()
                    cipher_info = ssock.cipher()
                    cipher_suite = cipher_info[0] if cipher_info else "Unknown"
                    alpn = ssock.selected_alpn_protocol()
                    subject = dict(x[0] for x in cert.get('subject', []))
                    issuer = dict(x[0] for x in cert.get('issuer', []))
                    san_list = [ext[1] for ext in cert.get('subjectAltName', []) if ext[0] == 'DNS']
                    return {"responded": True, "port": port, "tls_version": tls_version, "cipher_suite": cipher_suite, "alpn": alpn or "None", "cn": subject.get('commonName', ''), "organization": subject.get('organizationName', ''), "issuer_cn": issuer.get('commonName', ''), "san": san_list}
            except Exception: continue
        return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        targets = devices
        if context and "tcp" in context:
            tcp_ctx = context["tcp"]
            targets = [d for d in devices if tcp_ctx.get(d.ip) and any(str(p) in tcp_ctx[d.ip].raw_data.get("open_ports", []) for p in self.ports)]
        results = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                ip = futures[future]
                try: results[ip] = future.result()
                except Exception: results[ip] = FingerprintResult(source="https_cert", elapsed_ms=0.0)
        return results
