#!/usr/bin/env python3
"""
DHCP Cisco Collector — получение DHCP-leases с Cisco IOS через системный SSH-клиент.
Использует subprocess с флагами для совместимости со старыми алгоритмами Cisco IOS.
"""

from __future__ import annotations

import re
import subprocess
import time
from dataclasses import asdict
from typing import Dict

from config import CiscoDHCP
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class DHCPCiscoCollector(ActiveCollector):
    """
    Коллектор, который получает DHCP-leases с Cisco 3845 через системный SSH.
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
            # Формируем команду SSH с принудительным включением старых алгоритмов для Cisco IOS
            ssh_cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", f"ConnectTimeout={self.timeout}",
                "-o", "KexAlgorithms=+diffie-hellman-group1-sha1,diffie-hellman-group14-sha1",
                "-o", "HostKeyAlgorithms=+ssh-rsa,ssh-dss",
                "-o", "Ciphers=+aes128-cbc,3des-cbc,aes256-cbc",
            ]
            
            if CiscoDHCP.SSH_KEY_PATH:
                ssh_cmd.extend(["-i", CiscoDHCP.SSH_KEY_PATH])
                
            target = f"{CiscoDHCP.USERNAME}@{CiscoDHCP.IP}"
            
            # Команды для Cisco
            cisco_commands = "terminal length 0\nshow ip dhcp binding\nexit\n"
            
            # Если есть пароль, используем sshpass
            if CiscoDHCP.PASSWORD:
                # Проверяем наличие sshpass
                try:
                    subprocess.run(["sshpass", "-V"], capture_output=True, check=True)
                    ssh_cmd = ["sshpass", "-p", CiscoDHCP.PASSWORD] + ssh_cmd
                except FileNotFoundError:
                    print("      [ERROR] Утилита 'sshpass' не найдена. Установите её: sudo apt install sshpass")
                    print("      [INFO] Или настройте аутентификацию по SSH-ключу (SSH_KEY_PATH в .env)")
                    return {}
            
            ssh_cmd.append(target)
            
            # Выполняем команду
            process = subprocess.Popen(
                ssh_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=cisco_commands, timeout=CiscoDHCP.TIMEOUT)
            
            if process.returncode != 0:
                print(f"      [ERROR] DHCP Cisco Collector failed (code {process.returncode}): {stderr.strip()}")
                return {}
                
            # Парсим вывод
            self._leases_cache = self._parse_dhcp_binding(stdout)
            self._cache_timestamp = current_time
            return self._leases_cache

        except subprocess.TimeoutExpired:
            print("      [ERROR] DHCP Cisco Collector failed: timeout")
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
