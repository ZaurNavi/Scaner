#!/usr/bin/env python3
"""
HTTPS Certificate & TLS Fingerprint Collector.
Собирает данные сертификата + TLS Version, Cipher Suite, ALPN.
"""

from __future__ import annotations

import socket
import ssl
import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class HTTPSCertCollector(ActiveCollector):
    PRIORITY = 75
    RELIABILITY = 90

    def __init__(self):
        super().__init__(timeout=2.0)
        self.workers = 32
        self.ports = [443, 8443, 4443]

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        cached = cache_get(device.ip, "https_cert")
        if cached:
            return FingerprintResult(**cached, source="https_cert", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(
                source="https_cert",
                raw_data={"responded": False, "reason": "device_unavailable"},
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        tls_data = self._get_tls_fingerprint(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if tls_data:
            result = FingerprintResult(
                source="https_cert",
                raw_data=tls_data,
                elapsed_ms=elapsed_ms,
                capabilities=["supports_https", "supports_tls_fp"]
            )
        else:
            result = FingerprintResult(
                source="https_cert",
                raw_data={"responded": False, "reason": "no_https_or_timeout"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "https_cert", asdict(result))
        return result

    def _get_tls_fingerprint(self, ip: str) -> dict | None:
        for port in self.ports:
            try:
                # Создаем контекст, который НЕ проверяет сертификат (для самоподписанных)
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                
                # Оборачиваем сокет в SSL
                with context.wrap_socket(sock, server_hostname=ip) as ssock:
                    ssock.connect((ip, port))
                    cert = ssock.getpeercert()
                    
                    # === TLS FINGERPRINTING ===
                    tls_version = ssock.version()
                    cipher_info = ssock.cipher()
                    cipher_suite = cipher_info[0] if cipher_info else "Unknown"
                    alpn = ssock.selected_alpn_protocol()
                    
                    # === ПАРСИНГ СЕРТИФИКАТА ===
                    subject = dict(x[0] for x in cert['subject'])
                    issuer = dict(x[0] for x in cert['issuer'])
                    
                    cn = subject.get('commonName', '')
                    org = subject.get('organizationName', '')
                    issuer_cn = issuer.get('commonName', '')
                    
                    # SAN (Subject Alternative Name)
                    san_list = []
                    for ext in cert.get('subjectAltName', []):
                        if ext[0] == 'DNS':
                            san_list.append(ext[1])

                    return {
                        "responded": True,
                        "port": port,
                        "tls_version": tls_version,          # <-- НОВОЕ
                        "cipher_suite": cipher_suite,        # <-- НОВОЕ
                        "alpn": alpn or "None",              # <-- НОВОЕ
                        "cn": cn,
                        "organization": org,
                        "issuer_cn": issuer_cn,
                        "san": san_list
                    }
            except (socket.timeout, ssl.SSLError, ConnectionRefusedError):
                continue
            except Exception:
                continue
        return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        targets = devices
        if context and "tcp" in context:
            tcp_ctx = context["tcp"]
            targets = [
                d for d in devices 
                if tcp_ctx.get(d.ip) and any(str(p) in tcp_ctx[d.ip].raw_data.get("open_ports", []) for p in self.ports)
            ]

        results: dict[str, FingerprintResult] = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    results[ip] = future.result()
                except Exception:
                    results[ip] = FingerprintResult(source="https_cert", elapsed_ms=0.0)
        return results
