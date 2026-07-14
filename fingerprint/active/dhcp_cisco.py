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

from config import CiscoDHCP
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class DHCPCiscoCollector(ActiveCollector):
    """
    Коллектор, который получает DHCP-leases с Cisco 3845 через SSH.
    """

    PRIORITY = 30  # Очень высокий приоритет — базовая информация
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

        # Получаем leases (с кэшированием на уровне коллектора)
        leases = self._get_all_leases()
        elapsed_ms = (time.time() - start_time) * 1000

        # Ищем lease для текущего устройства
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
        """
        Получает все DHCP-leases с Cisco через SSH. Кэширует на CACHE_TTL секунд.
        """
        # Проверяем, настроены ли учетные данные
        if not CiscoDHCP.is_configured():
            # Тихо пропускаем, если не настроено (не спамим логи)
            return {}

        current_time = time.time()
        if self._leases_cache and (current_time - self._cache_timestamp) < CiscoDHCP.CACHE_TTL:
            return self._leases_cache

        try:
            # Создаем SSH-клиент
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Подключаемся (с ключом или паролем)
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
            
            # Выполняем команды
            commands = [
                "terminal length 0",  # Отключаем постраничный вывод
                "show ip dhcp binding",
            ]
            
            output = ""
            for cmd in commands:
                stdin, stdout, stderr = ssh.exec_command(cmd, timeout=self.timeout)
                output += stdout.read().decode('utf-8', errors='ignore')
            
            ssh.close()

            # Парсим вывод
            self._leases_cache = self._parse_dhcp_binding(output)
            self._cache_timestamp = current_time
            return self._leases_cache

        except Exception as e:
            print(f"      [ERROR] DHCP Cisco Collector failed: {e}")
            return {}

    def _parse_dhcp_binding(self, output: str) -> Dict[str, dict]:
        """
        Парсит вывод 'show ip dhcp binding'.
        
        Пример строки:
        192.168.1.10    0100.1a.2b.3c.4d.5e     Jul 15 2026 12:00 PM    Automatic  Active      0.0.0.0
        """
        leases = {}
        
        # Регулярка для парсинга
        pattern = r'(\d+\.\d+\.\d+\.\d+)\s+01([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+(.*?)\s+(Automatic|Manual)\s+(Active|Expired|Conflict)'
        
        for match in re.finditer(pattern, output):
            ip = match.group(1)
            client_id_raw = match.group(2)  # 001a.2b3c.4d5e
            lease_expiration = match.group(3).strip()
            lease_type = match.group(4)
            lease_state = match.group(5)
            
            # Конвертируем Client-ID в MAC
            mac = client_id_raw.replace('.', '').lower()
            mac_formatted = ':'.join(mac[i:i+2] for i in range(0, 12, 2))
            
            leases[ip] = {
                "responded": True,
                "ip": ip,
                "mac": mac_formatted,
                "lease_expiration": lease_expiration,
                "lease_type": lease_type,  # Automatic = DHCP, Manual = статика
                "lease_state": lease_state,  # Active, Expired, Conflict
            }
        
        return leases

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        """
        Сканируем все устройства, но SSH-подключение делаем только один раз.
        """
        # Если не настроено — сразу возвращаем пустой результат
        if not CiscoDHCP.is_configured():
            return {}
        
        results: dict[str, FingerprintResult] = {}
        
        # Предварительно получаем все leases (один раз)
        self._get_all_leases()
        
        for device in devices:
            results[device.ip] = self.collect(device)
        
        return results
