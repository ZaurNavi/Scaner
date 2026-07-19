#!/usr/bin/env python3
"""
DHCP Cisco Collector.
v1.7.1: Интеграция с Configuration Layer.
"""

from __future__ import annotations

import re
import time
from dataclasses import asdict
from typing import Dict

try:
    from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
except ImportError:
    pass # Обработка будет в runtime

from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set
from configuration import ConfigurationManager


class DHCPCiscoCollector(ActiveCollector):
    PRIORITY = 30
    RELIABILITY = 95

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.dhcp_cisco.timeout", 10.0)
        self.cache_ttl = self.config.get("collector.dhcp_cisco.cache_ttl", 300)
        self._leases_cache: Dict[str, dict] | None = None
        self._cache_timestamp: float = 0

    def _is_configured(self) -> bool:
        return bool(self.config.get("collector.dhcp_cisco.ip", ""))

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()
        cached = cache_get(device.ip, "dhcp_cisco")
        if cached:
            return FingerprintResult(**cached, source="dhcp_cisco", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(source="dhcp_cisco", raw_data={"responded": False, "reason": "device_unavailable"}, elapsed_ms=(time.time() - start_time) * 1000)

        leases = self._get_all_leases()
        elapsed_ms = (time.time() - start_time) * 1000
        device_lease = leases.get(device.ip)

        if device_lease:
            result = FingerprintResult(source="dhcp_cisco", raw_data=device_lease, elapsed_ms=elapsed_ms, capabilities=["supports_dhcp"])
        else:
            result = FingerprintResult(source="dhcp_cisco", raw_data={"responded": False, "reason": "no_lease_found", "ip": device.ip}, elapsed_ms=elapsed_ms)

        cache_set(device.ip, "dhcp_cisco", asdict(result))
        return result

    def _get_all_leases(self) -> Dict[str, dict]:
        if not self._is_configured():
            return {}

        current_time = time.time()
        if self._leases_cache is not None and (current_time - self._cache_timestamp) < self.cache_ttl:
            return self._leases_cache

        try:
            connect_params = {
                "device_type": "cisco_ios",
                "host": self.config.get("collector.dhcp_cisco.ip"),
                "port": self.config.get("collector.dhcp_cisco.port", 22),
                "username": self.config.get("collector.dhcp_cisco.username", ""),
                "timeout": self.timeout,
                "global_delay_factor": 1,
            }
            if self.config.get("collector.dhcp_cisco.ssh_key_path"):
                connect_params["use_keys"] = True
                connect_params["key_file"] = self.config.get("collector.dhcp_cisco.ssh_key_path")
            elif self.config.get("collector.dhcp_cisco.password"):
                connect_params["password"] = self.config.get("collector.dhcp_cisco.password")
            else:
                return {}

            if self.config.get("collector.dhcp_cisco.enable_password"):
                connect_params["secret"] = self.config.get("collector.dhcp_cisco.enable_password")

            with ConnectHandler(**connect_params) as net_connect:
                if self.config.get("collector.dhcp_cisco.enable_password"):
                    net_connect.enable()

                target_prefix = self.config.get("collector.dhcp_cisco.network_prefix", "192.168.1").rstrip('.')
                command = f"show ip dhcp binding | include {target_prefix}\\."
                output = net_connect.send_command(command, read_timeout=self.timeout)

                self._leases_cache = self._parse_dhcp_binding(output)
                self._cache_timestamp = current_time
                return self._leases_cache

        except Exception:
            return {}

    def _parse_dhcp_binding(self, output: str) -> Dict[str, dict]:
        leases = {}
        if not output.strip():
            return leases
        pattern = r'(\d+\.\d+\.\d+\.\d+)\s+01([0-9a-fA-F]{2}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{2})\s+(.*?)\s+(Automatic|Manual)'
        for match in re.finditer(pattern, output):
            ip, client_id_raw, lease_expiration, lease_type = match.groups()
            mac = ':'.join(client_id_raw.replace('.', '').lower()[i:i+2] for i in range(0, 12, 2))
            leases[ip] = {"responded": True, "ip": ip, "mac": mac, "lease_expiration": lease_expiration, "lease_type": lease_type}
        return leases

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        if not self._is_configured():
            return {}
        self._get_all_leases()
        return {device.ip: self.collect(device) for device in devices}
