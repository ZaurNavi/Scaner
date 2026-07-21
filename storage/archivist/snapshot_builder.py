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


# ==============================================================================
# Helper-функции для безопасного извлечения значений
# ==============================================================================

def _get_obs_value(obs) -> any:
    """
    Безопасно извлекает значение из Observation или UnifiedObservation.
    UnifiedObservation имеет normalized_value, Observation — только value.
    """
    return getattr(obs, 'normalized_value', None) or getattr(obs, 'value', None)


def _get_obs_confidence(obs) -> float:
    """
    Безопасно извлекает confidence из Observation или UnifiedObservation.
    """
    return getattr(obs, 'confidence', 0.5)


# ==============================================================================
# Основная функция
# ==============================================================================

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
        
        # Безопасно извлекаем значение и confidence
        value = _get_obs_value(obs)
        confidence = _get_obs_confidence(obs)
        
        # Маппим attribute в ObservationType
        obs_type = _map_attribute_to_type(obs.attribute, value)
        
        # Преобразуем значение в строку
        value_str = _format_value(value)
        
        observations.append(Observation(
            snapshot_id=snapshot_id,
            source=source_enum,
            key=obs.attribute,
            value=value_str,
            obs_type=obs_type,
            confidence=int(confidence * 100),  # Преобразуем float в int
        ))
    
    return observations


def _map_collector_to_source(collector_id: str) -> Source:
    """
    Маппит collector_id в Enum Source.
    
    ES-1.8.3: Используем только существующие значения Enum Source:
    ARP, DNS, MDNS, TTL, TCP, HTTP, SSDP, SNMP, PING, NETFLOW, OUI, MANUAL, IMPORT, UNKNOWN
    
    Для новых коллекторов (ssh, smb, wsd, etc.) мапим на Source.UNKNOWN.
    """
    mapping = {
        # Существующие значения Enum Source
        "dns": Source.DNS,
        "mdns": Source.MDNS,
        "ttl": Source.TTL,
        "tcp": Source.TCP,
        "http": Source.HTTP,
        "ssdp": Source.SSDP,
        "snmp": Source.SNMP,
        "traffic": Source.NETFLOW,
        "omada": Source.NETFLOW,  # Omada — сетевой трафик
        "vendor": Source.OUI,
    }
    # Все остальные коллекторы (ssh, smb, wsd, netbios, dns_sd, banners,
    # https_cert, favicon, ntp, lldp_cdp, dhcp_cisco, switch_port, scapy_fp)
    # мапятся на Source.UNKNOWN через mapping.get(..., Source.UNKNOWN)
    return mapping.get(collector_id.lower(), Source.UNKNOWN)


def _map_attribute_to_type(attribute: str, value: any) -> ObservationType:
    """Маппит attribute и value в ObservationType."""
    if isinstance(value, bool):  # bool проверяем ДО int, т.к. bool — подкласс int
        return ObservationType.BOOLEAN
    elif isinstance(value, str):
        return ObservationType.STRING
    elif isinstance(value, int):
        return ObservationType.INTEGER
    elif isinstance(value, float):
        return ObservationType.FLOAT
    elif isinstance(value, (list, dict)):
        return ObservationType.JSON
    else:
        return ObservationType.STRING


def _format_value(value: any) -> str:
    """Форматирует значение в строку для хранения."""
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    else:
        return str(value)
