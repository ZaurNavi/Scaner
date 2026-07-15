#!/usr/bin/env python3
"""
Traffic Collector — единая точка входа для получения данных о сетевой активности.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, List

from .models import TrafficInfo
from .registry import get_traffic_sources


class TrafficCollector:
    def collect_all(self, target_ips: List[str]) -> Dict[str, TrafficInfo]:
        """
        Собирает трафик для целевых IP за один проход.
        """
        start_time = time.time()
        sources = get_traffic_sources()
        cycle_timestamp = datetime.now()
        
        print(f"\n  [TRAFFIC] Collector initialized. Sources: {len(sources)}")
        
        merged_traffic: Dict[str, TrafficInfo] = {}

        # Инициализация
        for source in sources:
            source.initialize()

        try:
            for source in sources:
                source_name = source.get_name()
                try:
                    # Передаем единый timestamp
                    source_data = source.collect_all(cycle_timestamp, target_ips)
                    
                    for ip, traffic_info in source_data.items():
                        if ip not in merged_traffic:
                            merged_traffic[ip] = TrafficInfo(
                                ip=ip,
                                mac=traffic_info.mac,
                                cycle_timestamp=cycle_timestamp
                            )
                        
                        # Строгий merge: никогда не перезаписывать
                        self._merge_info(merged_traffic[ip], traffic_info, source_name)
                        
                except Exception as e:
                    print(f"      [TRAFFIC] ❌ Source '{source_name}' failed: {e}")
                    source.stats["errors"] += 1

            # Вывод статистики в консоль (вместо logger)
            for source in sources:
                print(f"      [TRAFFIC] {source.get_name().capitalize()}: "
                      f"{source.stats['devices']} devices, "
                      f"{source.stats['elapsed_ms']:.1f} ms, "
                      f"errors: {source.stats['errors']}")
            print(f"      [TRAFFIC] Merged: {len(merged_traffic)} devices")
            
        finally:
            # Завершение
            for source in sources:
                source.shutdown()

        return merged_traffic

    def _merge_info(self, target: TrafficInfo, source_info: TrafficInfo, source_name: str):
        """
        Инвариант: никогда не перезаписывать существующие данные.
        """
        # Обновляем статус источника
        target.source_status[source_name] = "ok" if source_info else "empty"
        
        for key, value in source_info.__dict__.items():
            if key in ("ip", "mac", "cycle_timestamp", "source_status"):
                continue
                
            if key == "sources_available":
                if value and value not in target.sources_available:
                    target.sources_available.append(value)
                continue
                
            if key == "raw_data":
                if value:
                    target.raw_data.update(value)
                continue
                
            # Если в target уже есть значение, или в source None — пропускаем
            if getattr(target, key) is not None:
                continue
            if value is None:
                continue
                
            setattr(target, key, value)


traffic_collector = TrafficCollector()
