#!/usr/bin/env python3
"""
DeviceCapabilities — унифицированное представление возможностей устройства.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class DeviceCapabilities:
    """
    Бинарные флаги возможностей устройства.
    True = обнаружено, False = не обнаружено, None = неизвестно
    """
    
    # Сетевые протоколы
    icmp: bool | None = None
    tcp: bool | None = None
    http: bool | None = None
    https: bool | None = None
    ssh: bool | None = None
    telnet: bool | None = None
    snmp: bool | None = None
    upnp: bool | None = None
    
    # Типы сервисов
    printer: bool | None = None
    camera: bool | None = None
    router: bool | None = None
    nas: bool | None = None
    media_player: bool | None = None
    iot_device: bool | None = None
    
    # Дополнительные
    firewall: bool | None = None
    sleeping: bool | None = None
    
    @classmethod
    def from_collected(cls, collected) -> DeviceCapabilities:
        """
        Создаёт DeviceCapabilities из CollectedData.
        """
        caps = cls()
        
        # TTL → ICMP
        ttl_result = collected.sources.get("ttl")
        if ttl_result:
            caps.icmp = ttl_result.raw_data.get("alive", False)
        
        # TCP → порты
        tcp_result = collected.sources.get("tcp")
        if tcp_result:
            ports = set(tcp_result.ports)
            caps.tcp = len(ports) > 0
            caps.http = 80 in ports or 8080 in ports
            caps.https = 443 in ports or 8443 in ports
            caps.ssh = 22 in ports
            caps.telnet = 23 in ports
            caps.snmp = 161 in ports
            caps.upnp = 1900 in ports
            caps.printer = 9100 in ports or 631 in ports
            caps.camera = 554 in ports or 8000 in ports
            caps.router = 8291 in ports or 8728 in ports
            caps.nas = 5000 in ports or 5001 in ports
        
        # HTTP → веб-интерфейс
        http_result = collected.sources.get("http")
        if http_result:
            caps.http = caps.http or (http_result.confidence > 0)
        
        return caps
    
    def summary(self) -> str:
        """
        Возвращает читаемое описание возможностей.
        """
        parts = []
        if self.icmp:
            parts.append("ICMP")
        if self.tcp:
            parts.append("TCP")
        if self.http:
            parts.append("HTTP")
        if self.ssh:
            parts.append("SSH")
        if self.printer:
            parts.append("Printer")
        if self.camera:
            parts.append("Camera")
        if self.router:
            parts.append("Router")
        
        return ", ".join(parts) if parts else "None"
