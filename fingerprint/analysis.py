#!/usr/bin/env python3
"""
Анализ собранных данных и применение эвристик.

Архитектура:
  Collectors → Evidence → Correlation Engine → Device
"""

from __future__ import annotations

from models import Device

from .collectors import CollectedData, collect_all
from .collectors.mdns import MDNSInfo
from .correlation import engine as correlation_engine


def _get_source(collected: CollectedData, source_name: str):
    return collected.sources.get(source_name)


def fingerprint_device(device: Device, collected: CollectedData) -> Device:
    """
    Применяет все методы fingerprint к устройству.
    """
    
    # 1. Hostname (mDNS > DNS)
    if collected.mdns.hostname:
        device.hostname = collected.mdns.hostname
    elif collected.hostname:
        device.hostname = collected.hostname
    
    # 2. Correlation Engine — ГЛАВНЫЙ источник решений
    corr_result = correlation_engine.correlate(device, collected)
    
    # 3. Применяем результаты корреляции (перезаписываем всё)
    if corr_result.os:
        device.os = corr_result.os
    if corr_result.model:
        device.model = corr_result.model
    if corr_result.device_type:
        device.device_type = corr_result.device_type
    if corr_result.vendor and corr_result.vendor != "Unknown":
        device.vendor = corr_result.vendor
    
    # 4. Финальный confidence — из breakdown
    device.confidence = corr_result.breakdown.total()
    
    # 5. Reason — из matched rules
    if corr_result.reasons:
        device.reason = "; ".join(corr_result.reasons[:2])
    
    return device


def fingerprint_all(
    devices: list[Device],
    collected_data: dict[str, CollectedData] | None = None,
) -> list[Device]:
    """
    Применяет fingerprint ко всем устройствам.
    """
    if not devices:
        return devices

    if collected_data is None:
        ips = [d.ip for d in devices]
        collected_data = collect_all(ips, devices)

    for device in devices:
        collected = collected_data.get(device.ip, CollectedData())
        fingerprint_device(device, collected)

    return devices
