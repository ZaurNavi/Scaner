#!/usr/bin/env python3
"""
Builder для формирования IdentityProfile из DeviceContext.
Не знает о Repository, History Service или БД.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import List, Dict, Set

from .models import (
    IdentityProfile, IdentityAttribute, IdentityStatistics, 
    TrafficStatistics, IdentityNetworkProfile, IdentityDeviceProfile,
    IdentityTimeline, DeviceContext
)


class IdentityBuilder:
    """Формирует IdentityProfile из DeviceContext."""
    
    def build(self, context: DeviceContext) -> IdentityProfile:
        """
        Строит IdentityProfile для устройства.
        Идемпотентный: повторный вызов даёт идентичный результат.
        """
        # Собираем данные через set для уникальности
        network_data = self._collect_network(context)
        device_data = self._collect_device(context)
        statistics = self._collect_statistics(context)
        traffic_stats = self._collect_traffic_statistics(context)
        
        # Создаём immutable профили
        network_profile = IdentityNetworkProfile(
            known_ips=tuple(network_data["ips"]),
            known_aps=tuple(network_data["aps"]),
            known_ssids=tuple(network_data["ssids"]),
            known_vlans=tuple(network_data["vlans"]),
            known_radios=tuple(network_data["radios"]),
            known_wifi_capabilities=tuple(network_data["wifi_capabilities"])
        )
        
        device_profile = IdentityDeviceProfile(
            known_vendors=tuple(device_data["vendors"]),
            known_models=tuple(device_data["models"]),
            known_operating_systems=tuple(device_data["operating_systems"]),
            known_device_types=tuple(device_data["device_types"]),
            known_hostnames=tuple(device_data["hostnames"]),
            known_macs=tuple(device_data["macs"])
        )
        
        timeline = IdentityTimeline(
            first_seen=context.first_seen,
            last_seen=context.last_seen
        )
        
        return IdentityProfile(
            identity_id=str(uuid.uuid4()),
            device_id=context.device_id,
            primary_mac=context.mac,
            timeline=timeline,
            network=network_profile,
            device=device_profile,
            statistics=statistics,
            traffic_statistics=traffic_stats,
            last_updated=datetime.now()
        )

    def _collect_network(self, context: DeviceContext) -> Dict[str, Set[IdentityAttribute]]:
        """Собирает сетевые атрибуты."""
        data = {
            "ips": set(),
            "aps": set(),
            "ssids": set(),
            "vlans": set(),
            "radios": set(),
            "wifi_capabilities": set()
        }
        
        # Из snapshots
        for snapshot in context.snapshots:
            if snapshot.ip:
                data["ips"].add(IdentityAttribute(
                    value=snapshot.ip,
                    first_seen=snapshot.timestamp,
                    last_seen=snapshot.timestamp,
                    sources=("snapshot",)
                ))
        
        # Из observations (Omada)
        for obs in context.observations:
            if obs.key == "omada" and obs.value:
                try:
                    omada_data = json.loads(obs.value)
                    entities = omada_data.get("entities", [])
                    for entity in entities:
                        ts = obs.timestamp or datetime.now()
                        
                        if entity.get("apName"):
                            data["aps"].add(IdentityAttribute(
                                value=entity["apName"],
                                first_seen=ts,
                                last_seen=ts,
                                sources=("omada",)
                            ))
                        
                        if entity.get("ssid"):
                            data["ssids"].add(IdentityAttribute(
                                value=entity["ssid"],
                                first_seen=ts,
                                last_seen=ts,
                                sources=("omada",)
                            ))
                        
                        if entity.get("vid"):
                            data["vlans"].add(IdentityAttribute(
                                value=str(entity["vid"]),
                                first_seen=ts,
                                last_seen=ts,
                                sources=("omada",)
                            ))
                        
                        radio_id = entity.get("radioId")
                        if radio_id is not None:
                            radio_map = {0: "2.4GHz", 1: "5GHz", 2: "6GHz"}
                            data["radios"].add(IdentityAttribute(
                                value=radio_map.get(radio_id, f"Radio{radio_id}"),
                                first_seen=ts,
                                last_seen=ts,
                                sources=("omada",)
                            ))
                        
                        wifi_mode = entity.get("wifiMode")
                        if wifi_mode is not None:
                            wifi_map = {0: "802.11b", 1: "802.11g", 2: "802.11a", 
                                       3: "802.11n", 4: "802.11ac", 5: "802.11ax"}
                            data["wifi_capabilities"].add(IdentityAttribute(
                                value=wifi_map.get(wifi_mode, f"Mode{wifi_mode}"),
                                first_seen=ts,
                                last_seen=ts,
                                sources=("omada",)
                            ))
                except:
                    pass
        
        return data

    def _collect_device(self, context: DeviceContext) -> Dict[str, Set[IdentityAttribute]]:
        """Собирает атрибуты устройства."""
        data = {
            "vendors": set(),
            "models": set(),
            "operating_systems": set(),
            "device_types": set(),
            "hostnames": set(),
            "macs": set()
        }
        
        # MAC
        data["macs"].add(IdentityAttribute(
            value=context.mac,
            first_seen=context.first_seen,
            last_seen=context.last_seen,
            sources=("device",)
        ))
        
        # Из snapshots
        for snapshot in context.snapshots:
            ts = snapshot.timestamp
            
            if snapshot.hostname:
                data["hostnames"].add(IdentityAttribute(
                    value=snapshot.hostname,
                    first_seen=ts,
                    last_seen=ts,
                    sources=("snapshot",)
                ))
            
            if snapshot.model:
                data["models"].add(IdentityAttribute(
                    value=snapshot.model,
                    first_seen=ts,
                    last_seen=ts,
                    sources=("snapshot",)
                ))
            
            if snapshot.os:
                data["operating_systems"].add(IdentityAttribute(
                    value=snapshot.os,
                    first_seen=ts,
                    last_seen=ts,
                    sources=("snapshot",)
                ))
            
            if snapshot.device_type:
                data["device_types"].add(IdentityAttribute(
                    value=snapshot.device_type,
                    first_seen=ts,
                    last_seen=ts,
                    sources=("snapshot",)
                ))
        
        return data

    def _collect_statistics(self, context: DeviceContext) -> IdentityStatistics:
        """Собирает статистику."""
        return IdentityStatistics(
            sessions_count=len(context.sessions),
            snapshots_count=len(context.snapshots),
            events_count=len(context.events)
        )

    def _collect_traffic_statistics(self, context: DeviceContext) -> TrafficStatistics:
        """Собирает статистику трафика."""
        # Пока не реализовано, требует интеграции с Traffic Collector
        return TrafficStatistics()
