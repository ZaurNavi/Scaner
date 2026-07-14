#!/usr/bin/env python3
"""
HTTPS Certificate Collector — извлечение информации из SSL-сертификата (порт 443).
"""

from __future__ import annotations

import socket
import ssl
import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID

from config import Fingerprint
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class HTTPSCertCollector(ActiveCollector):
    PRIORITY = 75  # После HTTP
    RELIABILITY = 90

    def __init__(self):
        super().__init__(timeout=2.0)
        self.workers = 32
        self.port = 443

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

        cert_data = self._get_cert(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if cert_data:
            result = FingerprintResult(source="https_cert", raw_data=cert_data, elapsed_ms=elapsed_ms)
        else:
            result = FingerprintResult(
                source="https_cert",
                raw_data={"responded": False, "reason": "no_cert_or_timeout"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "https_cert", asdict(result))
        return result

    def _get_cert(self, ip: str) -> dict | None:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((ip, self.port), timeout=self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=ip) as ssock:
                    der_cert = ssock.getpeercert(binary_form=True)
                    if not der_cert:
                        return None
                    
                    cert = x509.load_der_x509_certificate(der_cert, default_backend())
                    
                    cn = ""
                    try:
                        cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
                    except Exception:
                        pass

                    issuer = ""
                    try:
                        issuer = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
                    except Exception:
                        pass
                    
                    org = ""
                    try:
                        org = cert.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value
                    except Exception:
                        pass

                    return {
                        "responded": True,
                        "cn": cn,
                        "issuer": issuer,
                        "organization": org,
                        "not_valid_before": cert.not_valid_before_utc.isoformat(),
                        "not_valid_after": cert.not_valid_after_utc.isoformat(),
                    }
        except Exception:
            return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        """
        Запускаем только для устройств, у которых открыт порт 443 (из TCP context).
        """
        targets = []
        tcp_context = context.get("tcp", {}) if context else {}
        
        for d in devices:
            tcp_res = tcp_context.get(d.ip)
            if tcp_res and tcp_res.raw_data.get("open_ports"):
                ports = tcp_res.raw_data.get("open_ports", [])
                # Поддерживаем и int, и str в списке портов
                if 443 in ports or "443" in ports or 8443 in ports or "8443" in ports:
                    targets.append(d)
            elif not tcp_res:
                targets.append(d)

        results = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    results[ip] = future.result()
                except Exception:
                    results[ip] = FingerprintResult(source="https_cert", elapsed_ms=0.0)
        return results
