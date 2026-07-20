#!/usr/bin/env python3
"""
mDNS (Bonjour) Collector.
ES-1.8.3: Возвращает List[Observation] через ObservationFactory.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Any

from zeroconf import Zeroconf, ServiceBrowser
from configuration import ConfigurationManager
from .base import BasePassiveCollector
from .registry import passive_collector
from ..normalization import ObservationFactory


@dataclass
class MDNSInfo:
    hostname: str = ""
    model: str = ""
    device_type: str = ""
    services: list = field(default_factory=list)


class MDNSListener:
    def __init__(self, target_ips: set):
        self.target_ips = target_ips
        self.results: dict[str, MDNSInfo] = {}

    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if not info or not info.parsed_addresses():
            return

        for ip in info.parsed_addresses():
            if ip not in self.target_ips:
                continue

            if ip not in self.results:
                self.results[ip] = MDNSInfo()

            mdns_info = self.results[ip]

            if info.server and not mdns_info.hostname:
                mdns_info.hostname = info.server.rstrip(".")

            props = info.properties
            if not mdns_info.model:
                if b"model" in props:
                    mdns_info.model = props[b"model"].decode("utf-8", errors="ignore")
                elif b"ty" in props:
                    mdns_info.model = props[b"ty"].decode("utf-8", errors="ignore")

            if not mdns_info.device_type:
                if "_apple-mobdev2" in service_type or "_iphone" in service_type:
                    mdns_info.device_type = "iPhone"
                elif "_android" in service_type or "_adb" in service_type:
                    mdns_info.device_type = "Android Device"
                elif "_ipp" in service_type or "_printer" in service_type:
                    mdns_info.device_type = "Printer"
                elif "_googlecast" in service_type:
                    mdns_info.device_type = "Chromecast"
                elif "_airplay" in service_type or "_raop" in service_type:
                    mdns_info.device_type = "AirPlay Device"
                elif "_workstation" in service_type:
                    mdns_info.device_type = "Workstation"
                elif "_smb" in service_type:
                    mdns_info.device_type = "SMB Server"
                elif "_ssh" in service_type:
                    mdns_info.device_type = "SSH Server"
                elif "_http" in service_type or "_https" in service_type:
                    mdns_info.device_type = "HTTP Server"

            mdns_info.services.append(service_type)

    def update_service(self, zeroconf, service_type, name):
        pass

    def remove_service(self, zeroconf, service_type, name):
        pass


MDNS_SERVICE_TYPES = [
    "_apple-mobdev2._tcp.local.", "_airplay._tcp.local.", "_raop._tcp.local.",
    "_googlecast._tcp.local.", "_ipp._tcp.local.", "_printer._tcp.local.",
    "_http._tcp.local.", "_https._tcp.local.", "_adb._tcp.local.",
    "_android._tcp.local.", "_workstation._tcp.local.", "_device-info._tcp.local.",
    "_smb._tcp.local.", "_ssh._tcp.local.",
]


@passive_collector(
    id="mdns",
    name="mDNS Collector",
    version="1.0.0",
    protocol="mDNS",
    category="passive",
    priority=20,
    enabled_by_default=True,
    capabilities=("mdns_discovery", "service_detection")
)
class MDNSCollector(BasePassiveCollector):
    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("fingerprint.collectors.mdns.timeout", 2.0)

    def observe(self, ips: List[str], context: dict[str, Any] = None) -> List:
        """ES-1.8.3: Возвращает List[Observation]."""
        if not ips:
            return []

        target_ips = set(ips)
        zeroconf = Zeroconf()
        listener = MDNSListener(target_ips)

        try:
            browsers = []
            for service_type in MDNS_SERVICE_TYPES:
                browser = ServiceBrowser(zeroconf, service_type, listener)
                browsers.append(browser)
            time.sleep(self.timeout)
        finally:
            zeroconf.close()

        observations = []
        for ip, mdns_info in listener.results.items():
            if mdns_info.hostname:
                obs = ObservationFactory.create_hostname(
                    collector_id=self.id,
                    protocol=self.protocol,
                    device_id=ip,
                    hostname=mdns_info.hostname
                )
                observations.append(obs)
            
            if mdns_info.model:
                obs = ObservationFactory.create(
                    collector_id=self.id,
                    protocol=self.protocol,
                    device_id=ip,
                    attribute="model",
                    value=mdns_info.model
                )
                observations.append(obs)
            
            if mdns_info.device_type:
                obs = ObservationFactory.create(
                    collector_id=self.id,
                    protocol=self.protocol,
                    device_id=ip,
                    attribute="device_type",
                    value=mdns_info.device_type
                )
                observations.append(obs)
            
            if mdns_info.services:
                obs = ObservationFactory.create(
                    collector_id=self.id,
                    protocol=self.protocol,
                    device_id=ip,
                    attribute="services",
                    value=mdns_info.services
                )
                observations.append(obs)

        return observations
