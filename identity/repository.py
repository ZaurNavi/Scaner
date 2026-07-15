#!/usr/bin/env python3
"""
Repository для работы с Identity в Archivist.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, List

from .models import IdentityProfile, IdentityAttribute, IdentityStatistics, TrafficStatistics, IdentityNetworkProfile, IdentityDeviceProfile, IdentityTimeline


class IdentityRepository:
    """Единственный слой взаимодействия с Archivist для Identity."""
    
    def __init__(self, db_manager):
        self.db = db_manager

    def load_identity(self, device_id: str) -> Optional[IdentityProfile]:
        """Загружает IdentityProfile из БД."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, device_id, mac, metadata
            FROM identity
            WHERE device_id = ?
        """, (device_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        identity_id, dev_id, mac, metadata_json = row
        
        if metadata_json:
            try:
                metadata = json.loads(metadata_json)
                return self._dict_to_profile(identity_id, dev_id, mac, metadata)
            except json.JSONDecodeError:
                return None
        
        return None

    def save_identity(self, profile: IdentityProfile):
        """Сохраняет новую IdentityProfile в БД."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO identity (id, device_id, mac, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            profile.identity_id,
            profile.device_id,
            profile.primary_mac,
            json.dumps(profile.to_dict())
        ))
        conn.commit()

    def update_identity(self, profile: IdentityProfile):
        """Обновляет существующую IdentityProfile."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE identity
            SET mac = ?, metadata = ?
            WHERE device_id = ?
        """, (
            profile.primary_mac,
            json.dumps(profile.to_dict()),
            profile.device_id
        ))
        conn.commit()

    def exists(self, device_id: str) -> bool:
        """Проверяет существование Identity для устройства."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM identity WHERE device_id = ?
        """, (device_id,))
        count = cursor.fetchone()[0]
        return count > 0

    def _dict_to_profile(self, identity_id: str, device_id: str, mac: str, metadata: dict) -> IdentityProfile:
        """Восстанавливает IdentityProfile из словаря."""
        def deserialize_attributes(attrs_data: List[Dict]) -> tuple:
            return tuple(
                IdentityAttribute(
                    value=attr["value"],
                    first_seen=datetime.fromisoformat(attr["first_seen"]),
                    last_seen=datetime.fromisoformat(attr["last_seen"]),
                    sources=tuple(attr.get("sources", []))
                )
                for attr in attrs_data
            )
        
        timeline_data = metadata.get("timeline", {})
        network_data = metadata.get("network", {})
        device_data = metadata.get("device", {})
        stats_data = metadata.get("statistics", {})
        traffic_data = metadata.get("traffic_statistics", {})
        
        return IdentityProfile(
            identity_id=identity_id,
            device_id=device_id,
            schema_version=metadata.get("schema_version", 1),
            identity_version=metadata.get("identity_version", 1),
            primary_mac=mac,
            timeline=IdentityTimeline(
                first_seen=datetime.fromisoformat(timeline_data["first_seen"]),
                last_seen=datetime.fromisoformat(timeline_data["last_seen"])
            ),
            network=IdentityNetworkProfile(
                known_ips=deserialize_attributes(network_data.get("known_ips", [])),
                known_aps=deserialize_attributes(network_data.get("known_aps", [])),
                known_ssids=deserialize_attributes(network_data.get("known_ssids", [])),
                known_vlans=deserialize_attributes(network_data.get("known_vlans", [])),
                known_radios=deserialize_attributes(network_data.get("known_radios", [])),
                known_wifi_capabilities=deserialize_attributes(network_data.get("known_wifi_capabilities", []))
            ),
            device=IdentityDeviceProfile(
                known_vendors=deserialize_attributes(device_data.get("known_vendors", [])),
                known_models=deserialize_attributes(device_data.get("known_models", [])),
                known_operating_systems=deserialize_attributes(device_data.get("known_operating_systems", [])),
                known_device_types=deserialize_attributes(device_data.get("known_device_types", [])),
                known_hostnames=deserialize_attributes(device_data.get("known_hostnames", [])),
                known_macs=deserialize_attributes(device_data.get("known_macs", []))
            ),
            statistics=IdentityStatistics(
                sessions_count=stats_data.get("sessions_count", 0),
                snapshots_count=stats_data.get("snapshots_count", 0),
                events_count=stats_data.get("events_count", 0)
            ),
            traffic_statistics=TrafficStatistics(
                total_download=traffic_data.get("total_download", 0),
                total_upload=traffic_data.get("total_upload", 0),
                total_traffic=traffic_data.get("total_traffic", 0),
                total_packets=traffic_data.get("total_packets", 0),
                total_flows=traffic_data.get("total_flows", 0)
            ),
            last_updated=datetime.fromisoformat(metadata["last_updated"]),
            metadata=metadata.get("metadata", {})
        )
