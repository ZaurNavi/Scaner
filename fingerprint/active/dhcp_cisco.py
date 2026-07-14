#!/usr/bin/env python3
"""
DHCP Cisco Collector — получение DHCP-leases с Cisco IOS через SSH.
Выполняет команду 'show ip dhcp binding' и парсит вывод.
"""

from __future__ import annotations

import re
import time
from dataclasses import asdict
from typing import Dict

import paramiko

# ==============================================================================
# FIX для Cisco IOS 15.x: Разрешаем устаревшие алгоритмы Key Exchange (KEX).
# Современные версии paramiko блокируют их по умолчанию из соображений безопасности.
# ==============================================================================
paramiko.transport.Transport._preferred_kex = (
    "diffie-hellman-group14-sha1",
    "diffie-hellman-group1-sha1",
    "ecdh-sha2-nistp256",
    "ecdh-sha2-nistp384",
    "ecdh-sha2-nistp521",
    "diffie-hellman-group-exchange-sha256",
    "diffie-hellman-group-exchange-sha1",
)
# ==============================================================================

from config import CiscoDHCP
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class DHCPCiscoCollector(ActiveCollector):
    """
    Коллектор, который получает DHCP-leases с Cisco 3845 через SSH.
    """

    PRIORITY = 30
    RELIABILITY = 95

    def __init__(self):
        super().__init__(timeout=CiscoDHCP.TIMEOUT)
        self._leases_cache: Dict[str, dict] | None = None
        self._cache_timestamp: float = 0

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        cached = cache_get(device.ip, "dhcp_cisco")
        if cached:
            return FingerprintResult(**cached, source="dhcp_cisco", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(
                source="dhcp_cisco",
                raw_data={"responded": False, "reason": "device_unavailable"},
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        leases = self._get_all_leases()
        elapsed_ms = (time.time() - start_time) * 1000

        device_lease = leases.get(device.ip)

        if device_lease:
            result = FingerprintResult(
                source="dhcp_cisco",
                raw_data=device_lease,
                elapsed_ms=elapsed_ms,
                capabilities=["supports_dhcp"]
            )
        else:
            result = FingerprintResult(
                source="dhcp_cisco",
                raw_data={"responded": False, "reason": "no_lease_found", "ip": device.ip},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "dhcp_cisco", asdict(result))
        return result

    def _get_all_leases(self) -> Dict[str, dict]:
        if not CiscoDHCP.is_configured():
            return {}

        current_time = time.time()
        if self._leases_cache and (current_time - self._cache_timestamp) < CiscoDHCP.CACHE_TTL:
            return self._leases_cache

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                "hostname": CiscoDHCP.IP,
                "port": CiscoDHCP.PORT,
                "username": CiscoDHCP.USERNAME,
                "timeout": self.timeout,
                "allow_agent": False,
                "look_for_keys": False,
            }
            
            if CiscoDHCP.SSH_KEY_PATH:
                connect_kwargs["key_filename"] = CiscoDHCP.SSH_KEY_PATH
            elif CiscoDHCP.PASSWORD:
                connect_kwargs["password"] = CiscoDHCP.PASSWORD
            else:
                return {}
            
            ssh.connect(**connect_kwargs)
            
            commands = [
                "terminal length 0",
                "show ip dhcp binding",
            ]
            
            output = ""
            for cmd in commands:
                stdin, stdout, stderr = ssh.exec_command(cmd, timeout=self.timeout)
                output += stdout.read().decode('utf-8', errors='ignore')
            
            ssh.close()

            self._leases_cache = self._parse_dhcp_binding(output)
            self._cache_timestamp = current_time
            return self._leases_cache

        except Exception as e:
            print(f"      [ERROR] DHCP Cisco Collector failed: {e}")
            return {}

    def _parse_dhcp_binding(self, output: str) -> Dict[str, dict]:
        leases = {}
        pattern = r'(\d+\.\d+\.\d+\.\d+)\s+01([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+(.*?)\s+(Automatic|Manual)\s+(Active|Expired|Conflict)'
        
        for match in re.finditer(pattern, output):
            ip = match.group(1)
            client_id_raw = match.group(2)
            lease_expiration = match.group(3).strip()
            lease_type = match.group(4)
            lease_state = match.group(5)
            
            mac = client_id_raw.replace('.', '').lower()
            mac_formatted = ':'.join(mac[i:i+2] for i in range(0, 12, 2))
            
            leases[ip] = {
                "responded": True,
                "ip": ip,
                "mac": mac_formatted,
                "lease_expiration": lease_expiration,
                "lease_type": lease_type,
                "lease_state": lease_state,
            }
        
        return leases

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        if not CiscoDHCP.is_configured():
            return {}
        
        results: dict[str, FingerprintResult] = {}
        self._get_all_leases()
        
        for device in devices:
            results[device.ip] = self.collect(device)
        
        return results
