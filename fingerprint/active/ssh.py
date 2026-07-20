#!/usr/bin/env python3
"""
SSH Banner Collector.
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

import socket
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


class SSHCollector(ActiveCollector):
    PRIORITY = 51
    RELIABILITY = 90

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.ssh.timeout", 1.0)
        self.port = self.config.get("collector.ssh.port", 22)

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

        banner = self._get_banner(device.ip)
        if banner:
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="SSH",
                device_id=device.ip,
                attribute="banner",
                value=banner
            )]
        return []

    def _get_banner(self, ip: str) -> str | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, self.port))
            banner = sock.recv(128).decode('utf-8', errors='ignore').strip()
            sock.close()
            return banner if banner.startswith("SSH-") else None
        except Exception:
            return None
