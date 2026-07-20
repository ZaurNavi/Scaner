#!/usr/bin/env python3
"""
HTTPS Certificate & TLS Fingerprint Collector.
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

import socket
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


class HTTPSCertCollector(ActiveCollector):
    PRIORITY = 75
    RELIABILITY = 90

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.https_cert.timeout", 2.0)
        self.workers = self.config.get("collector.https_cert.workers", 32)
        ports_str = self.config.get("collector.https_cert.ports", "443,8443,4443")
        self.ports = [int(p) for p in ports_str.split(",")]

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

        tls_data = self._get_tls_fingerprint(device.ip)
        if tls_data:
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="TLS",
                device_id=device.ip,
                attribute="tls_cert_info",
                value=tls_data
            )]
        return []

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> list:
        """ES-1.8.3: scan теперь возвращает List[Observation] для всех устройств."""
        all_observations = []
        targets = devices
        if context and "tcp" in context:
            tcp_ctx = context["tcp"]
            targets = [d for d in devices if tcp_ctx.get(d.ip) and any(str(p) in tcp_ctx[d.ip].raw_data.get("open_ports", []) for p in self.ports)]

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in targets}
            for future in as_completed(futures):
                try:
                    all_observations.extend(future.result())
                except Exception:
                    pass
        return all_observations

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
                    return {
                        "responded": True, "port": port, "tls_version": tls_version,
                        "cipher_suite": cipher_suite, "alpn": alpn or "None",
                        "cn": subject.get('commonName', ''), "organization": subject.get('organizationName', ''),
                        "issuer_cn": issuer.get('commonName', ''), "san": san_list
                    }
            except Exception:
                continue
        return None
