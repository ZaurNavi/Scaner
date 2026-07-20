#!/usr/bin/env python3
"""
Snapshot Builder — строит SnapshotBundle из UnifiedObservationBatch.
ES-1.8.3: Полная миграция на UnifiedObservationBatch.
Удалены зависимости от CollectedData и FingerprintResult.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict

from models import Device
from fingerprint import UnifiedObservationBatch
from fingerprint.normalization.models import ObservationCategory

from storage.schema import (
    SnapshotBundle, Scan, Device as DomainDevice, Snapshot,
    Observation, Evidence, CollectorLog,
    DeviceStatus, DeviceType, Source, ObservationType, CollectorStatus
)


def build_snapshot_bundle(
    device: Device,
    scan: Scan,
    batch: UnifiedObservationBatch,
) -> SnapshotBundle:
    """
    ES-1.8.3: Строит SnapshotBundle из UnifiedObservationBatch.
    Один Bundle = одно устройство = одна транзакция.
    """

    # 1. Domain Device (паспорт)
    domain_device = DomainDevice(
        mac=device.mac,
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        status=DeviceStatus.ACTIVE,
    )

    # 2. Snapshot (снимок состояния)
    snapshot = Snapshot(
        scan_id=scan.id,
        device_id=domain_device.id,
        timestamp=datetime.now(),
        ip=device.ip,
        hostname=device.hostname or "",
        os=device.os or "",
        model=device.model or "",
        device_type=_map_device_type(device.device_type),
        confidence=device.confidence,
    )

    # 3. Observations из batch
    observations = _build_observations(snapshot.id, device.ip, batch)

    # 4. Evidence (пока пустой, так как correlation engine требует миграции)
    evidence = []

    # 5. CollectorLog
    total_elapsed = batch.metadata.get("elapsed_ms", 0.0) if batch.metadata else 0.0
    collector_log = CollectorLog(
        scan_id=scan.id,
        collector_name="fingerprint_engine",
        started_at=scan.started_at,
        finished_at=datetime.now(),
        duration_ms=total_elapsed,
        objects_processed=batch.count(),
        status=CollectorStatus.SUCCESS,
        warnings=0,
        error_message="",
    )

    # 6. Собираем Bundle
    return SnapshotBundle(
        scan_id=scan.id,
        snapshot=snapshot,
        scan=scan,
        device=domain_device,
        observations=tuple(observations),
        evidence=tuple(evidence),
        collector_log=collector_log,
    )


def _map_device_type(device_type: str) -> DeviceType:
    """Маппит строку device_type в Enum DeviceType."""
    if not device_type:
        return DeviceType.UNKNOWN
    mapping = {
        "router": DeviceType.ROUTER,
        "switch": DeviceType.SWITCH,
        "access_point": DeviceType.ACCESS_POINT,
        "phone": DeviceType.PHONE,
        "smartphone": DeviceType.PHONE,
        "tablet": DeviceType.TABLET,
        "laptop": DeviceType.LAPTOP,
        "desktop": DeviceType.DESKTOP,
        "printer": DeviceType.PRINTER,
        "camera": DeviceType.CAMERA,
        "tv": DeviceType.TV,
        "iot": DeviceType.IOT,
        "server": DeviceType.SERVER,
        "network device": DeviceType.ROUTER,
    }
    return mapping.get(device_type.lower(), DeviceType.UNKNOWN)


def _build_observations(snapshot_id: str, ip: str, batch: UnifiedObservationBatch) -> list[Observation]:
    """
    ES-1.8.3: Собирает Observations из UnifiedObservationBatch.
    Использует Query API для извлечения данных.
    """
    observations = []
    
    # Фильтруем observations для этого IP
    device_batch = batch.filter(lambda obs: obs.metadata.ip == ip)
    
    for obs in device_batch:
        # Маппим collector_id в Source enum
        source_enum = _map_collector_to_source(obs.collector_id)
        
        # Маппим attribute в ObservationType
        obs_type = _map_attribute_to_type(obs.attribute, obs.normalized_value)
        
        # Преобразуем значение в строку
        value = _format_value(obs.normalized_value)
        
        observations.append(Observation(
            snapshot_id=snapshot_id,
            source=source_enum,
            key=obs.attribute,
            value=value,
            obs_type=obs_type,
            confidence=int(obs.confidence * 100),  # Преобразуем float в int
        ))
    
    return observations


def _map_collector_to_source(collector_id: str) -> Source:
    """Маппит collector_id в Enum Source."""
    mapping = {
        "dns": Source.DNS,
        "mdns": Source.MDNS,
        "tcp": Source.TCP,
        "http": Source.HTTP,
        "ssh": Source.SSH,
        "smb": Source.SMB,
        "snmp": Source.SNMP,
        "ssdp": Source.SSDP,
        "wsd": Source.WSD,
        "netbios": Source.NETBIOS,
        "dns_sd": Source.DNS_SD,
        "ttl": Source.TTL,
        "scapy_fp": Source.SCAY_FP,
        "banners": Source.BANNERS,
        "https_cert": Source.HTTPS_CERT,
        "favicon": Source.FAVICON,
        "ntp": Source.NTP,
        "lldp_cdp": Source.LLDP_CDP,
        "dhcp_cisco": Source.DHCP_CISCO,
        "switch_port": Source.SWITCH_PORT,
        "traffic": Source.NETFLOW,
        "omada": Source.OMADA,
    }
    return mapping.get(collector_id.lower(), Source.UNKNOWN)


def _map_attribute_to_type(attribute: str, value: any) -> ObservationType:
    """Маппит attribute и value в ObservationType."""
    if isinstance(value, str):
        return ObservationType.STRING
    elif isinstance(value, int):
        return ObservationType.INTEGER
    elif isinstance(value, float):
        return ObservationType.FLOAT
    elif isinstance(value, bool):
        return ObservationType.BOOLEAN
    elif isinstance(value, (list, dict)):
        return ObservationType.JSON
    else:
        return ObservationType.STRING


def _format_value(value: any) -> str:
    """Форматирует значение в строку для хранения."""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    else:
        return str(value)
