from __future__ import annotations
from datetime import datetime
from typing import Dict

from models import Device
from fingerprint.collectors.base import CollectedData
from fingerprint.correlation import engine as correlation_engine

from storage.schema import (
    SnapshotBundle, Scan, Device as DomainDevice, Snapshot,
    Observation, Evidence, CollectorLog,
    DeviceStatus, DeviceType, Source, ObservationType, CollectorStatus
)


def build_snapshot_bundle(
    device: Device,
    scan: Scan,
    collected: CollectedData,
) -> SnapshotBundle:
    """
    Строит SnapshotBundle из данных устройства и собранных фактов.
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

    # 3. Observations из collected_data
    observations = _build_observations(snapshot.id, collected)

    # 4. Evidence из correlation engine
    evidence = _build_evidence(snapshot.id, device, collected)

    # 5. CollectorLog
    total_elapsed = sum(src.elapsed_ms for src in collected.sources.values())
    collector_log = CollectorLog(
        scan_id=scan.id,
        collector_name="fingerprint_engine",
        started_at=scan.started_at,
        finished_at=datetime.now(),
        duration_ms=total_elapsed,
        objects_processed=len(collected.sources),
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


def _build_observations(snapshot_id: str, collected: CollectedData) -> list[Observation]:
    """
    Собирает Observations из ВСЕХ источников.
    Универсальный обработчик для всех коллекторов.
    """
    observations = []

    # === СПЕЦИАЛЬНАЯ ОБРАБОТКА (для источников с особой структурой) ===

    # TTL
    if "ttl" in collected.sources:
        ttl_result = collected.sources["ttl"]
        if ttl_result.ttl:
            observations.append(Observation(
                snapshot_id=snapshot_id,
                source=Source.TTL,
                key="ttl",
                value=str(ttl_result.ttl),
                obs_type=ObservationType.INTEGER,
                confidence=ttl_result.confidence,
            ))

    # TCP ports
    if "tcp" in collected.sources:
        tcp_result = collected.sources["tcp"]
        if tcp_result.services:
            observations.append(Observation(
                snapshot_id=snapshot_id,
                source=Source.TCP,
                key="open_ports",
                value=str(list(tcp_result.services.keys())),
                obs_type=ObservationType.JSON,
                confidence=tcp_result.confidence,
            ))

    # HTTP
    if "http" in collected.sources:
        http_result = collected.sources["http"]
        for port, data in http_result.services.items():
            if isinstance(data, dict):
                if data.get("server"):
                    observations.append(Observation(
                        snapshot_id=snapshot_id,
                        source=Source.HTTP,
                        key=f"http.server.port_{port}",
                        value=data["server"],
                        obs_type=ObservationType.STRING,
                        confidence=http_result.confidence,
                    ))

    # mDNS
    if collected.mdns.hostname:
        observations.append(Observation(
            snapshot_id=snapshot_id,
            source=Source.MDNS,
            key="hostname",
            value=collected.mdns.hostname,
            obs_type=ObservationType.STRING,
            confidence=35,
        ))

    # DNS hostname
    if collected.hostname:
        observations.append(Observation(
            snapshot_id=snapshot_id,
            source=Source.DNS,
            key="hostname",
            value=collected.hostname,
            obs_type=ObservationType.STRING,
            confidence=10,
        ))

    # === АВТОМАТИЧЕСКАЯ ОБРАБОТКА ВСЕХ ОСТАЛЬНЫХ ИСТОЧНИКОВ ===
    # Теперь нам НЕ НУЖНО вручную перечислять каждый коллектор!
    # Любой источник, который вернул responded=True, автоматически сохраняется.
    # Это делает систему устойчивой к добавлению новых коллекторов.
    
    # Источники, которые мы уже обработали выше (специальная обработка)
    already_processed = {"ttl", "tcp", "http"}
    
    for source_name, result in collected.sources.items():
        if source_name in already_processed:
            continue
        
        # Сохраняем любой источник, который ответил
        if result.raw_data.get("responded"):
            source_enum = _map_source_string_to_enum(source_name)
            observations.append(Observation(
                snapshot_id=snapshot_id,
                source=source_enum,
                key=source_name,
                value=str(result.raw_data),
                obs_type=ObservationType.JSON,
                confidence=result.confidence,
            ))

    return observations


def _map_source_string_to_enum(source_name: str) -> Source:
    """Маппит строку source_name в Enum Source."""
    mapping = {
        "snmp": Source.SNMP,
        "ssdp": Source.SSDP,
        "ttl": Source.TTL,
        "tcp": Source.TCP,
        "http": Source.HTTP,
        "mdns": Source.MDNS,
        "dns": Source.DNS,
    }
    return mapping.get(source_name.lower(), Source.UNKNOWN)


def _build_evidence(snapshot_id: str, device: Device, collected: CollectedData) -> list[Evidence]:
    """Собирает Evidence из correlation engine."""
    corr_result = correlation_engine.correlate(device, collected)

    evidence_list = []
    for item in corr_result.evidence_items:
        evidence_list.append(Evidence(
            snapshot_id=snapshot_id,
            description=item.description,
            contribution=item.contribution,
            source=_map_source(item.source),
            details=item.details or "",
        ))

    return evidence_list


def _map_source(source_str: str) -> Source:
    """Маппит строку source в Enum Source."""
    mapping = {
        "vendor": Source.OUI,
        "hostname": Source.DNS,
        "ttl": Source.TTL,
        "tcp": Source.TCP,
        "http": Source.HTTP,
        "mdns": Source.MDNS,
        "ssdp": Source.SSDP,
        "snmp": Source.SNMP,
        "arp": Source.ARP,
        "netflow": Source.NETFLOW,
    }
    if source_str.startswith("rule:"):
        return Source.UNKNOWN
    return mapping.get(source_str.lower(), Source.UNKNOWN)
