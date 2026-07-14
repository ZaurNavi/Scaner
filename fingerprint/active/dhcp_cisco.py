#!/usr/bin/env python3
"""
DHCP Cisco Collector — получение DHCP-leases с Cisco IOS через Netmiko.
Использует фильтрацию на стороне роутера для получения данных только по целевой сети.
"""

from __future__ import annotations

import re
import time
from dataclasses import asdict
from typing import Dict

try:
    from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
except ImportError:
    print("      [ERROR] Netmiko не установлен. Выполните: pip install netmiko")
    raise

from config import CiscoDHCP, Network
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class DHCPCiscoCollector(ActiveCollector):
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
            cached_dict = dict(cached)
            cached_dict["source"] = "dhcp_cisco"
            cached_dict["elapsed_ms"] = 0.0
            return FingerprintResult(**cached_dict)

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
        # ИСПРАВЛЕНИЕ 2: Правильная проверка кэша (пустой словарь {} тоже должен считаться кэшем)
        if self._leases_cache is not None and (current_time - self._cache_timestamp) < CiscoDHCP.CACHE_TTL:
            return self._leases_cache

        try:
            connect_params = {
                "device_type": "cisco_ios",
                "host": CiscoDHCP.IP,
                "port": CiscoDHCP.PORT,
                "username": CiscoDHCP.USERNAME,
                "timeout": self.timeout,
                "global_delay_factor": 1,
            }
            
            if CiscoDHCP.SSH_KEY_PATH:
                connect_params["use_keys"] = True
                connect_params["key_file"] = CiscoDHCP.SSH_KEY_PATH
            elif CiscoDHCP.PASSWORD:
                connect_params["password"] = CiscoDHCP.PASSWORD
            else:
                return {}
            
            if CiscoDHCP.ENABLE_PASSWORD:
                connect_params["secret"] = CiscoDHCP.ENABLE_PASSWORD

            with ConnectHandler(**connect_params) as net_connect:
                if CiscoDHCP.ENABLE_PASSWORD:
                    net_connect.enable()
                
                target_prefix = Network.PREFIX.rstrip('.')
                command = f"show ip dhcp binding | include {target_prefix}\\."
                
                output = net_connect.send_command(command, read_timeout=self.timeout)
                
                print(f"\n      [DEBUG DHCP] Executed on Cisco: '{command}'")
                print(f"      [DEBUG DHCP] Raw output ({len(output)} chars):")
                print("      " + "-" * 60)
                if output.strip():
                    for line in output.strip().split('\n')[:15]:
                        print(f"      | {line.strip()}")
                else:
                    print("      | (no bindings found for this subnet)")
                print("      " + "-" * 60)
                
                self._leases_cache = self._parse_dhcp_binding(output)
                self._cache_timestamp = current_time
                
                print(f"      [DEBUG DHCP] Successfully parsed {len(self._leases_cache)} leases!")
                if self._leases_cache:
                    for ip, data in list(self._leases_cache.items())[:3]:
                        print(f"         -> {ip}: mac={data.get('mac')}, type={data.get('lease_type')}, expires={data.get('lease_expiration')}")
                
                return self._leases_cache

        except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
            print(f"      [ERROR] DHCP Cisco Collector failed (Auth/Timeout): {e}")
            return {}
        except Exception as e:
            print(f"      [ERROR] DHCP Cisco Collector failed: {e}")
            return {}

    def _parse_dhcp_binding(self, output: str) -> Dict[str, dict]:
        leases = {}
        if not output.strip():
            return leases
        
        # ИСПРАВЛЕНИЕ 1: Точная регулярка под формат Cisco: 01 + 2 символа . 4 символа . 4 символа . 2 символа
        # Пример: 01be.5633.5176.b3
        pattern = r'(\d+\.\d+\.\d+\.\d+)\s+01([0-9a-fA-F]{2}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{2})\s+(.*?)\s+(Automatic|Manual)'
        
        for match in re.finditer(pattern, output):
            ip = match.group(1)
            client_id_raw = match.group(2)
            lease_expiration = match.group(3).strip()
            lease_type = match.group(4)
            
            # Преобразуем be.5633.5176.b3 в be:56:33:51:76:b3
            mac = client_id_raw.replace('.', '').lower()
            mac_formatted = ':'.join(mac[i:i+2] for i in range(0, 12, 2))
            
            leases[ip] = {
                "responded": True,
                "ip": ip,
                "mac": mac_formatted,
                "lease_expiration": lease_expiration,
                "lease_type": lease_type,
            }
        
        return leases

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        if not CiscoDHCP.is_configured():
            return {}
        
        results: dict[str, FingerprintResult] = {}
        
        # Получаем данные ОДИН раз для всех устройств
        self._get_all_leases()
        
        for device in devices:
            results[device.ip] = self.collect(device)
        
        return results
