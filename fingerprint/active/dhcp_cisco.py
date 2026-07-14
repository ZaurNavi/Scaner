#!/usr/bin/env python3
"""
DHCP Cisco Collector — получение DHCP-leases с Cisco IOS через Netmiko.
Netmiko автоматически обрабатывает устаревшие алгоритмы SSH для старых Cisco IOS.
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

from config import CiscoDHCP
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class DHCPCiscoCollector(ActiveCollector):
    """
    Коллектор, который получает DHCP-leases с Cisco 3845 через Netmiko.
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
            # Исправление TypeError: безопасно обновляем поля из кэша
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
        if self._leases_cache and (current_time - self._cache_timestamp) < CiscoDHCP.CACHE_TTL:
            return self._leases_cache

        try:
            # Настройка устройства для Netmiko
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
            
            # Если нужен enable пароль
            if CiscoDHCP.ENABLE_PASSWORD:
                connect_params["secret"] = CiscoDHCP.ENABLE_PASSWORD

            # Подключение через Netmiko (он сам разберется с legacy алгоритмами Cisco)
            with ConnectHandler(**connect_params) as net_connect:
                # Если нужен enable, входим в него
                if CiscoDHCP.ENABLE_PASSWORD:
                    net_connect.enable()
                
                # Выполняем команду
                output = net_connect.send_command("show ip dhcp binding", read_timeout=self.timeout)
                
                # Парсим вывод
                self._leases_cache = self._parse_dhcp_binding(output)
                self._cache_timestamp = current_time
                return self._leases_cache

        except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
            print(f"      [ERROR] DHCP Cisco Collector failed (Auth/Timeout): {e}")
            return {}
        except Exception as e:
            print(f"      [ERROR] DHCP Cisco Collector failed: {e}")
            return {}

    def _parse_dhcp_binding(self, output: str) -> Dict[str, dict]:
        leases = {}
        # Регулярка для парсинга вывода 'show ip dhcp binding'
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
