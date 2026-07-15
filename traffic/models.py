#!/usr/bin/env python3
"""
Модели данных для Traffic Collector.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TrafficInfo:
    """
    Универсальная модель описания сетевой активности устройства.
    Никогда не вычисляет значения. Если источник знает поле — оно копируется, иначе None.
    """
    # Идентификаторы (Пункт 3)
    ip: str | None = None
    mac: str | None = None
    
    # Метаданные
    cycle_timestamp: datetime | None = None  # (Пункт 4)
    sources_available: list[str] = field(default_factory=list)
    source_status: dict[str, str] = field(default_factory=dict)  # (Пункт 2)
    
    # === NetFlow / sFlow / IPFIX ===
    # (Пункт 7: используем total, если агрегатор не разделяет up/down)
    netflow_bytes_total: int | None = None
    netflow_packets_total: int | None = None
    netflow_flows: int | None = None
    netflow_first_seen: datetime | None = None
    netflow_last_seen: datetime | None = None
    
    # === Omada / Controller Telemetry ===
    omada_uptime: int | None = None
    omada_last_activity: datetime | None = None
    omada_bytes_down: int | None = None
    omada_bytes_up: int | None = None
    omada_packets_down: int | None = None
    omada_packets_up: int | None = None
    omada_tx_rate: float | None = None
    omada_rx_rate: float | None = None
    omada_rssi: int | None = None
    omada_signal: int | None = None
    omada_snr: int | None = None
    omada_channel: int | None = None
    omada_radio: str | None = None
    omada_wifi_mode: str | None = None
    omada_power_save: bool | None = None
    
    # (Пункт 14: сырые данные для отладки и Behaviour Engine)
    raw_data: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Компактная конвертация в словарь для Archivist (Пункт 9)."""
        result = {}
        for key, value in self.__dict__.items():
            if value is None:
                continue
            if isinstance(value, list) and len(value) == 0:
                continue
            if isinstance(value, dict) and len(value) == 0:
                continue
                
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
