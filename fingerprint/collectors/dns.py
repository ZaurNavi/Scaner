#!/usr/bin/env python3
from __future__ import annotations
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Any
from configuration import ConfigurationManager
from .base import BasePassiveCollector
from .registry import passive_collector
from ..normalization import ObservationFactory, ObservationCategory

@passive_collector(
    id="dns", name="DNS Collector", version="1.0.0", protocol="DNS",
    category="passive", priority=10, enabled_by_default=True,
    capabilities=("dns_resolution", "hostname_discovery"),
    default_category="identity"
)
class DNSCollector(BasePassiveCollector):
    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.workers = self.config.get("fingerprint.collectors.dns.workers", 32)

    def _resolve_single(self, ip: str) -> str:
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except (socket.herror, socket.gaierror, OSError):
            return ""

    # ES-1.8.3: Возвращает ТОЛЬКО List[Observation]
    def observe(self, ips: List[str], context: dict[str, Any] = None) -> List:
        if not ips: return []
        
        observations = []
        workers = min(self.workers, len(ips))
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self._resolve_single, ip): ip for ip in ips}
            for future in as_completed(futures):
                ip = futures[future]
                hostname = future.result()
                if hostname:
                    obs = ObservationFactory.create_hostname(
                        collector_id=self.id, protocol=self.protocol, device_id=ip, hostname=hostname
                    )
                    observations.append(obs)
        return observations
