#!/usr/bin/env python3
"""
DHCP Cisco Collector — получение DHCP bindings через SSH к Cisco роутеру.
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

import re
import time
from typing import Dict

try:
    from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
except ImportError:
    pass  # Обработка будет в runtime

from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


class DHCPCiscoCollector(ActiveCollector):
    PRIORITY = 30
    RELIABILITY = 95

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.dhcp_cisco.timeout", 10.0)
        self.cache_ttl = self.config.get("collector.dhcp_cisco.cache_ttl", 300)
        # Бизнес-кэш данных с роутера (не кэш результатов!)
        self._leases_cache: Dict[str, dict] | None = None
        self._cache_timestamp: float = 0

    def _is_configured(self) -> bool:
        return bool(self.config.get("collector.dhcp_cisco.ip", ""))

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

        leases = self._get_all_leases()
        device_lease = leases.get(device.ip)
        
        if device_lease:
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="DHCP",
                device_id=device.ip,
                attribute="dhcp_lease",
                value=device_lease
            )]
        return []

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> list:
        """ES-1.8.3: scan возвращает List[Observation] для всех устройств."""
        if not self._is_configured():
            return []
        
        # Загружаем все leases один раз
        self._get_all_leases()
        
        all_observations = []
        for device in devices:
            if self.is_available(device):
                all_observations.extend(self.collect(device))
        return all_observations

    def _get_all_leases(self) -> Dict[str, dict]:
        """Внутренний бизнес-кэш данных с роутера (сохранён из оригинала)."""
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
            leases[ip] = {
                "responded": True, 
                "ip": ip, 
                "mac": mac, 
                "lease_expiration": lease_expiration, 
                "lease_type": lease_type
            }
        return leases
