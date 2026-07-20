#!/usr/bin/env python3
from __future__ import annotations
from models import Device
from .base import ActiveCollector
from .ping import ping
from configuration import ConfigurationManager
from ..normalization import ObservationFactory

class TTLCollector(ActiveCollector):
    PRIORITY = 40
    RELIABILITY = 20
    
    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.ttl.timeout", 1.0)
        self.count = self.config.get("collector.ttl.count", 1)

    def collect(self, device: Device) -> list:
        if not self.is_available(device): return []

        ping_result = ping(device.ip, timeout=self.timeout, count=self.count)
        
        if ping_result.alive and ping_result.ttl:
            return [ObservationFactory.create_ttl(
                collector_id=self.source_name, protocol="ICMP", device_id=device.ip, 
                ttl=ping_result.ttl, latency=ping_result.latency_ms or 0.0
            )]
        return []
