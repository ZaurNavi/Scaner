#!/usr/bin/env python3
"""
Модели данных для Identity Engine.
Все модели immutable после создания.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class IdentityAttribute:
    """Атрибут Identity с временными метками и источниками."""
    value: str
    first_seen: datetime
    last_seen: datetime
    sources: tuple = field(default_factory=tuple)  # immutable


@dataclass(frozen=True)
class IdentityNetworkProfile:
    """Сетевой профиль устройства."""
    known_ips: tuple = field(default_factory=tuple)
    known_aps: tuple = field(default_factory=tuple)
    known_ssids: tuple = field(default_factory=tuple)
    known_vlans: tuple = field(default_factory=tuple)
    known_radios: tuple = field(default_factory=tuple)
    known_wifi_capabilities: tuple = field(default_factory=tuple)


@dataclass(frozen=True)
class IdentityDeviceProfile:
    """Профиль устройства (характеристики)."""
    known_vendors: tuple = field(default_factory=tuple)
    known_models: tuple = field(default_factory=tuple)
    known_operating_systems: tuple = field(default_factory=tuple)
    known_device_types: tuple = field(default_factory=tuple)
    known_hostnames: tuple = field(default_factory=tuple)
    known_macs: tuple = field(default_factory=tuple)


@dataclass(frozen=True)
class IdentityStatistics:
    """Агрегированная статистика устройства."""
    sessions_count: int = 0
    snapshots_count: int = 0
    events_count: int = 0


@dataclass(frozen=True)
class TrafficStatistics:
    """Агрегированная статистика трафика."""
    total_download: int = 0
    total_upload: int = 0
    total_traffic: int = 0
    total_packets: int = 0
    total_flows: int = 0


@dataclass(frozen=True)
class IdentityTimeline:
    """Временная шкала Identity."""
    first_seen: datetime
    last_seen: datetime


@dataclass(frozen=True)
class IdentityProfile:
    """Полная карточка устройства (Identity). Immutable."""
    # Идентификаторы
    identity_id: str
    device_id: str
    
    # Версионирование
    schema_version: int = 1
    identity_version: int = 1
    
    # Основной MAC
    primary_mac: str
    
    # Временные характеристики
    timeline: IdentityTimeline
    
    # Профили
    network: IdentityNetworkProfile
    device: IdentityDeviceProfile
    
    # Статистика
    statistics: IdentityStatistics
    traffic_statistics: TrafficStatistics
    
    # Метаданные
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация для сохранения в БД."""
        def serialize_attributes(attrs: tuple) -> List[Dict]:
            return [
                {
                    "value": attr.value,
                    "first_seen": attr.first_seen.isoformat(),
                    "last_seen": attr.last_seen.isoformat(),
                    "sources": list(attr.sources)
                }
                for attr in attrs
            ]
        
        return {
            "schema_version": self.schema_version,
            "identity_version": self.identity_version,
            "primary_mac": self.primary_mac,
            "timeline": {
                "first_seen": self.timeline.first_seen.isoformat(),
                "last_seen": self.timeline.last_seen.isoformat()
            },
            "network": {
                "known_ips": serialize_attributes(self.network.known_ips),
                "known_aps": serialize_attributes(self.network.known_aps),
                "known_ssids": serialize_attributes(self.network.known_ssids),
                "known_vlans": serialize_attributes(self.network.known_vlans),
                "known_radios": serialize_attributes(self.network.known_radios),
                "known_wifi_capabilities": serialize_attributes(self.network.known_wifi_capabilities)
            },
            "device": {
                "known_vendors": serialize_attributes(self.device.known_vendors),
                "known_models": serialize_attributes(self.device.known_models),
                "known_operating_systems": serialize_attributes(self.device.known_operating_systems),
                "known_device_types": serialize_attributes(self.device.known_device_types),
                "known_hostnames": serialize_attributes(self.device.known_hostnames),
                "known_macs": serialize_attributes(self.device.known_macs)
            },
            "statistics": {
                "sessions_count": self.statistics.sessions_count,
                "snapshots_count": self.statistics.snapshots_count,
                "events_count": self.statistics.events_count
            },
            "traffic_statistics": {
                "total_download": self.traffic_statistics.total_download,
                "total_upload": self.traffic_statistics.total_upload,
                "total_traffic": self.traffic_statistics.total_traffic,
                "total_packets": self.traffic_statistics.total_packets,
                "total_flows": self.traffic_statistics.total_flows
            },
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class DeviceContext:
    """Контекст устройства для Builder."""
    device_id: str
    mac: str
    first_seen: datetime
    last_seen: datetime
    snapshots: List[Any] = field(default_factory=list)
    observations: List[Any] = field(default_factory=list)
    events: List[Any] = field(default_factory=list)
    sessions: List[Any] = field(default_factory=list)
