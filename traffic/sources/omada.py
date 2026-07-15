#!/usr/bin/env python3
"""
Omada Traffic Source для Traffic Collector.
"""

from __future__ import annotations

import time
import logging
from datetime import datetime

from .base import TrafficSource
from ..models import TrafficInfo

try:
    from fingerprint.controllers.omada import OmadaCollector
    from fingerprint.controllers.registry import get_controller_collectors
except ImportError:
    OmadaCollector = None
    get_controller_collectors = None


class OmadaTrafficSource(TrafficSource):
    def __init__(self):
        super().__init__()
        self.priority = 20
        self._collector = None

    def get_name(self) -> str:
        return "omada"

    def is_available(self) -> bool:
        if OmadaCollector is None:
            return False
        
        if self._collector is None:
            collectors = get_controller_collectors() if get_controller_collectors else []
            for c in collectors:
                if isinstance(c, OmadaCollector) and c.is_enabled():
                    self._collector = c
                    return True
        return self._collector is not None

    def collect_all(self, cycle_timestamp: datetime, target_ips: list[str]) -> dict[str, TrafficInfo]:
        start_time = time.time()
        results = {}
        
        if not self.is_available():
            self.stats["errors"] += 1
            return results

        try:
            data = self._collector.collect()
            if "error" in data:
                self.stats["errors"] += 1
                return results

            for entity in data.get("clients", []):
                ip = entity.get("ip")
                if not ip:
                    continue
                
                # (Пункт 1: фильтрация)
                if target_ips and ip not in target_ips:
                    continue

                last_activity = None
                if entity.get("lastSeen"):
                    try:
                        last_activity = datetime.fromtimestamp(entity["lastSeen"] / 1000.0)
                    except Exception:
                        pass

                # (Пункт 8: чистый словарь вместо математики)
                radio_id = entity.get("radioId")
                radio_map = {0: "2.4GHz", 1: "5GHz", 2: "6GHz"}
                radio_name = radio_map.get(radio_id) if radio_id is not None else None

                wifi_map = {0: "802.11b", 1: "802.11g", 2: "802.11a", 3: "802.11n", 4: "802.11ac", 5: "802.11ax"}
                wifi_mode = wifi_map.get(entity.get("wifiMode"))

                results[ip] = TrafficInfo(
                    ip=ip,
                    mac=entity.get("mac", "").replace("-", ":"),
                    cycle_timestamp=cycle_timestamp,
                    omada_uptime=entity.get("uptime"),
                    omada_last_activity=last_activity,
                    omada_bytes_down=entity.get("trafficDown"),
                    omada_bytes_up=entity.get("trafficUp"),
                    omada_packets_down=entity.get("downPacket"),
                    omada_packets_up=entity.get("upPacket"),
                    omada_tx_rate=entity.get("txRate"),
                    omada_rx_rate=entity.get("rxRate"),
                    omada_rssi=entity.get("rssi"),
                    omada_signal=entity.get("signalLevel"),
                    omada_snr=entity.get("snr"),
                    omada_channel=entity.get("channel"),
                    omada_radio=radio_name,
                    omada_wifi_mode=wifi_mode,
                    omada_power_save=entity.get("powerSave"),
                    raw_data={"omada": entity}  # (Пункт 14)
                )
                
            self.stats["devices"] = len(results)
            
        except Exception as e:
            self.stats["errors"] += 1
            logging.error(f"Omada source error: {e}")
            
        finally:
            self.stats["elapsed_ms"] = (time.time() - start_time) * 1000
            
        return results
