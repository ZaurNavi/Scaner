#!/usr/bin/env python3
"""
Парсер для данных Omada Controller.
Используется Mobility Engine для извлечения RSSI, AP, SNR и т.д.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class OmadaClientRecord:
    """Распарсенная запись клиента Omada."""
    timestamp: datetime
    mac: str
    hostname: str | None
    ap_name: str | None
    ap_mac: str | None
    ssid: str | None
    rssi: int | None
    snr: int | None
    channel: int | None
    radio: str | None
    tx_rate: float | None
    rx_rate: float | None
    wifi_mode: str | None
    traffic_down: int | None
    traffic_up: int | None
    uptime: int | None


class OmadaParser:
    """Парсер для observations от Omada Controller."""

    @staticmethod
    def parse_observations(observations: list[Any]) -> list[OmadaClientRecord]:
        """
        Парсит список ObservationRecord от Omada.
        
        Args:
            observations: Список observations с source='UNKNOWN' и key='omada'
        
        Returns:
            Список распарсенных записей клиентов
        """
        records = []

        for obs in observations:
            if obs.source != "UNKNOWN" or obs.key != "omada":
                continue

            try:
                data = json.loads(obs.value)
                entities = data.get("entities", [])
                
                for entity in entities:
                    records.append(
                        OmadaClientRecord(
                            timestamp=obs.timestamp,
                            mac=entity.get("mac", ""),
                            hostname=entity.get("hostName") or entity.get("name"),
                            ap_name=entity.get("apName"),
                            ap_mac=entity.get("apMac"),
                            ssid=entity.get("ssid"),
                            rssi=entity.get("rssi"),
                            snr=entity.get("snr"),
                            channel=entity.get("channel"),
                            radio=OmadaParser._get_radio_name(entity.get("radioId")),
                            tx_rate=entity.get("txRate"),
                            rx_rate=entity.get("rxRate"),
                            wifi_mode=OmadaParser._get_wifi_mode(entity.get("wifiMode")),
                            traffic_down=entity.get("trafficDown"),
                            traffic_up=entity.get("trafficUp"),
                            uptime=entity.get("uptime"),
                        )
                    )
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"[OmadaParser] Error parsing observation: {e}")
                continue

        return records

    @staticmethod
    def _get_radio_name(radio_id: int | None) -> str | None:
        """Конвертирует radioId в понятное имя."""
        if radio_id is None:
            return None
        radio_map = {0: "2.4GHz", 1: "5GHz", 2: "6GHz"}
        return radio_map.get(radio_id, f"Radio{radio_id}")

    @staticmethod
    def _get_wifi_mode(wifi_mode: int | None) -> str | None:
        """Конвертирует wifiMode в стандарт WiFi."""
        if wifi_mode is None:
            return None
        mode_map = {
            0: "802.11b",
            1: "802.11g",
            2: "802.11a",
            3: "802.11n",
            4: "802.11ac",
            5: "802.11ax",
        }
        return mode_map.get(wifi_mode, f"Mode{wifi_mode}")
