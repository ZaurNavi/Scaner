#!/usr/bin/env python3
"""
NetFlow Source для Traffic Collector.
"""

from __future__ import annotations

import time
from datetime import datetime

from .base import TrafficSource
from ..models import TrafficInfo

try:
    from netflow import aggregate_netflow
except ImportError:
    aggregate_netflow = None


class NetFlowSource(TrafficSource):
    def __init__(self):
        super().__init__()
        self.priority = 10  # (Пункт 10)

    def get_name(self) -> str:
        return "netflow"

    def is_available(self) -> bool:
        return aggregate_netflow is not None

    def collect_all(self, cycle_timestamp: datetime, target_ips: list[str]) -> dict[str, TrafficInfo]:
        start_time = time.time()
        results = {}
        
        if not self.is_available():
            self.stats["errors"] += 1
            return results

        try:
            netflow_data = aggregate_netflow()
            
            for ip, data in netflow_data.items():
                # (Пункт 1: фильтруем по target_ips)
                if target_ips and ip not in target_ips:
                    continue

                first_seen = None
                if data.get("first_seen"):
                    try:
                        first_seen = datetime.fromisoformat(data["first_seen"].replace("Z", "+00:00"))
                    except Exception:
                        pass

                results[ip] = TrafficInfo(
                    ip=ip,
                    cycle_timestamp=cycle_timestamp,
                    netflow_bytes_total=data.get("bytes", 0),  # (Пункт 7)
                    netflow_packets_total=data.get("packets", 0),
                    netflow_flows=data.get("flows", 0),
                    netflow_first_seen=first_seen,
                    raw_data={"netflow": data}  # (Пункт 14)
                )
                
            self.stats["devices"] = len(results)
            
        except Exception as e:
            self.stats["errors"] += 1
            import logging
            logging.error(f"NetFlow source error: {e}")
            
        finally:
            self.stats["elapsed_ms"] = (time.time() - start_time) * 1000
            
        return results
