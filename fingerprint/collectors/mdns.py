#!/usr/bin/env python3
"""
mDNS (Bonjour) Collector.
ES-1.8.0: Passive Framework Implementation.
ES-1.8.2: Добавлена default_category для Normalization Layer.

Zero Knowledge Principle:
- Не знает о Platform Core
- Не знает о Knowledge Layer
- Не знает о Event Engine
- Только собирает mDNS данные
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any

from zeroconf import Zeroconf, ServiceBrowser

from configuration import ConfigurationManager

from .base import BasePassiveCollector, Observation
from .registry import passive_collector


# ==============================================================================
# MDNSInfo — Domain Model (Category B)
# ==============================================================================

@dataclass
class MDNSInfo:
    """
    Информация, полученная через mDNS.
    
    Domain Model (Category B) — остаётся без изменений.
    """
    hostname: str = ""
    model: str = ""
    device_type: str = ""
    services: list = field(default_factory=list)


# ==============================================================================
# MDNSListener — внутренняя реализация (Category C)
# ==============================================================================

class MDNSListener:
    """
    Слушает mDNS-ответы от всех устройств.
    
    Algorithm (Category C) — остаётся без изменений.
    """
    
    def __init__(self, target_ips: set):
        self.target_ips = target_ips
        self.results: Dict[str, MDNSInfo] = {}
    
    def add_service(self, zeroconf, service_type, name):
        """Вызывается при обнаружении сервиса."""
        info = zeroconf.get_service_info(service_type, name)
        
        if not info or not info.parsed_addresses():
            return
        
        for ip in info.parsed_addresses():
            if ip not in self.target_ips:
                continue
            
            if ip not in self.results:
                self.results[ip] = MDNSInfo()
            
            mdns_info = self.results[ip]
            
            # Извлекаем hostname
            if info.server and not mdns_info.hostname:
                mdns_info.hostname = info.server.rstrip(".")
            
            # Извлекаем модель из properties
            props = info.properties
            
            if not mdns_info.model:
                if b"model" in props:
                    mdns_info.model = props[b"model"].decode("utf-8", errors="ignore")
                elif b"ty" in props:  # Apple использует "ty"
                    mdns_info.model = props[b"ty"].decode("utf-8", errors="ignore")
            
            # Определяем тип устройства по сервису
            if not mdns_info.device_type:
                if "_apple-mobdev2" in service_type or "_iphone" in service_type:
                    mdns_info.device_type = "iPhone"
                elif "_android" in service_type or "_adb" in service_type:
                    mdns_info.device_type = "Android Device"
                elif "_ipp" in service_type or "_printer" in service_type:
                    mdns_info.device_type = "Printer"
                elif "_googlecast" in service_type:
                    mdns_info.device_type = "Chromecast"
                elif "_airplay" in service_type or "_raop" in service_type:
                    mdns_info.device_type = "AirPlay Device"
                elif "_workstation" in service_type:
                    mdns_info.device_type = "Workstation"
                elif "_smb" in service_type:
                    mdns_info.device_type = "SMB Server"
                elif "_ssh" in service_type:
                    mdns_info.device_type = "SSH Server"
                elif "_http" in service_type or "_https" in service_type:
                    mdns_info.device_type = "HTTP Server"
            
            mdns_info.services.append(service_type)
    
    def update_service(self, zeroconf, service_type, name):
        """Вызывается при обновлении сервиса. Пустой метод."""
        pass
    
    def remove_service(self, zeroconf, service_type, name):
        """Вызывается при удалении сервиса. Пустой метод."""
        pass


# ==============================================================================
# Service Types (Category B — Domain Constants)
# ==============================================================================

MDNS_SERVICE_TYPES = [
    "_apple-mobdev2._tcp.local.", "_airplay._tcp.local.", "_raop._tcp.local.",
    "_googlecast._tcp.local.", "_ipp._tcp.local.", "_printer._tcp.local.",
    "_http._tcp.local.", "_https._tcp.local.", "_adb._tcp.local.",
    "_android._tcp.local.", "_workstation._tcp.local.", "_device-info._tcp.local.",
    "_smb._tcp.local.", "_ssh._tcp.local.",
]


# ==============================================================================
# MDNSCollector — Passive Collector
# ==============================================================================

@passive_collector(
    id="mdns",
    name="mDNS Collector",
    version="1.0.0",
    protocol="mDNS",
    category="passive",
    priority=20,  # Запускается после DNS
    enabled_by_default=True,
    capabilities=("mdns_discovery", "service_detection"),
    default_category="discovery"  # ES-1.8.2: mDNS — это DISCOVERY, а не IDENTITY
)
class MDNSCollector(BasePassiveCollector):
    """
    mDNS (Bonjour) коллектор.
    
    v1.8.0: Наследует BasePassiveCollector, реализует observe().
    v1.8.2: Указывает default_category для нормализации.
    Все настройки получаются через ConfigurationManager.
    """
    
    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        # v1.8.0: Настройки из Configuration Layer
        self.timeout = self.config.get("fingerprint.collectors.mdns.timeout", 2.0)
    
    def observe(self, ips: List[str], context: Dict[str, Any] = None) -> Dict[str, Observation]:
        """
        Сканирует всю сеть через mDNS один раз.
        
        Args:
            ips: Список IP-адресов
            context: Не используется (Zero Knowledge Principle)
        
        Returns:
            Dict[ip, Observation] где Observation.data = MDNSInfo
        """
        if not ips:
            return {}
        
        target_ips = set(ips)
        zeroconf = Zeroconf()
        listener = MDNSListener(target_ips)
        timestamp = datetime.now()
        
        try:
            # Сохраняем ссылки на browser,
            # иначе объекты будут уничтожены GC и сканирование остановится.
            browsers = []
            
            for service_type in MDNS_SERVICE_TYPES:
                browser = ServiceBrowser(zeroconf, service_type, listener)
                browsers.append(browser)
            
            # Ждём ответа от устройств
            time.sleep(self.timeout)
        
        finally:
            zeroconf.close()
        
        # Преобразуем результаты в Observation
        result: Dict[str, Observation] = {}
        for ip, mdns_info in listener.results.items():
            result[ip] = Observation(
                collector_id=self.id,
                protocol=self.protocol,
                timestamp=timestamp,
                data=mdns_info,
                metadata={
                    "ip": ip,
                    "services_count": str(len(mdns_info.services)),
                    "hostname": mdns_info.hostname
                }
            )
        
        return result


# ==============================================================================
# Обратная совместимость — legacy функция collect_mdns
# ==============================================================================

def collect_mdns(ips: List[str]) -> Dict[str, MDNSInfo]:
    """
    Legacy функция для обратной совместимости.
    
    v1.8.0: Использует MDNSCollector через PassiveRegistry.
    """
    from configuration import get_config_manager
    
    config = get_config_manager()
    collector = MDNSCollector(config)
    observations = collector.observe(ips)
    
    # Преобразуем Observation в dict[ip, MDNSInfo]
    return {ip: obs.data for ip, obs in observations.items()}
