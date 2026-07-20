#!/usr/bin/env python3
"""
DNS Collector — Reverse DNS resolution.
ES-1.8.0: Passive Framework Implementation.
ES-1.8.2: Добавлена default_category для Normalization Layer.

Zero Knowledge Principle:
- Не знает о Platform Core
- Не знает о Knowledge Layer
- Не знает о Event Engine
- Только собирает hostname через reverse DNS
"""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Any

from configuration import ConfigurationManager

from .base import BasePassiveCollector, Observation
from .registry import passive_collector


@passive_collector(
    id="dns",
    name="DNS Collector",
    version="1.0.0",
    protocol="DNS",
    category="passive",
    priority=10,  # Запускается первым
    enabled_by_default=True,
    capabilities=("dns_resolution", "hostname_discovery"),
    default_category="identity"  # ES-1.8.2: Категория для нормализации
)
class DNSCollector(BasePassiveCollector):
    """
    Reverse DNS коллектор.
    
    v1.8.0: Наследует BasePassiveCollector, реализует observe().
    v1.8.2: Указывает default_category для нормализации.
    Все настройки получаются через ConfigurationManager.
    """
    
    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        # v1.8.0: Настройки из Configuration Layer
        self.workers = self.config.get("fingerprint.collectors.dns.workers", 32)
    
    def _resolve_single(self, ip: str) -> tuple[str, str]:
        """
        Резолвит один IP через reverse DNS.
        Возвращает (ip, hostname).
        """
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return ip, hostname
        except (socket.herror, socket.gaierror, OSError):
            return ip, ""
    
    def observe(self, ips: List[str], context: Dict[str, Any] = None) -> Dict[str, Observation]:
        """
        Наблюдает за сетью и возвращает hostname для каждого IP.
        
        Args:
            ips: Список IP-адресов
            context: Не используется (Zero Knowledge Principle)
        
        Returns:
            Dict[ip, Observation] где Observation.data = hostname
        """
        if not ips:
            return {}
        
        result: Dict[str, Observation] = {}
        workers = min(self.workers, len(ips))
        timestamp = datetime.now()
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._resolve_single, ip): ip
                for ip in ips
            }
            
            for future in as_completed(futures):
                ip, hostname = future.result()
                result[ip] = Observation(
                    collector_id=self.id,
                    protocol=self.protocol,
                    timestamp=timestamp,
                    data=hostname,
                    metadata={"ip": ip}
                )
        
        return result


# ==============================================================================
# Обратная совместимость — legacy функция collect_hostnames
# ==============================================================================

def collect_hostnames(ips: List[str]) -> Dict[str, str]:
    """
    Legacy функция для обратной совместимости.
    
    v1.8.0: Использует DNSCollector через PassiveRegistry.
    """
    from configuration import get_config_manager
    
    config = get_config_manager()
    collector = DNSCollector(config)
    observations = collector.observe(ips)
    
    # Преобразуем Observation в dict[ip, hostname]
    return {ip: obs.data for ip, obs in observations.items()}
