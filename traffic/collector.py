#!/usr/bin/env python3
"""
Traffic Collector — единая точка входа для получения данных о сетевой активности.
"""

from __future__ import annotations

import time
import logging
from datetime import datetime
from typing import Dict, List

from .models import TrafficInfo
from .registry import get_traffic_sources

logger = logging.getLogger(__name__)


class TrafficCollector:
    def collect_all(self, target_ips: List[str]) -> Dict[str, TrafficInfo]:
        """
        Собирает трафик для целевых IP за один проход.
        """
        start_time = time.time()
        sources = get_traffic_sources()
        cycle_timestamp = datetime.now()  # (Пункт 4)
        
        logger.info(f"Traffic Collector initialized. Sources: {len(sources)}")
        
        merged_traffic: Dict[str, TrafficInfo] = {}

        # (Пункт 11) Инициализация
        for source in sources:
            source.initialize()

        try:
            for source in sources:
                source_name = source.get_name()
                try:
                    # (Пункт 4) Передаем единый timestamp
                    source_data = source.collect_all(cycle_timestamp, target_ips)
                    
                    for ip, traffic_info in source_data.items():
                        if ip not in merged_traffic:
                            merged_traffic[ip] = TrafficInfo(
                                ip=ip,
                                mac=traffic_info.mac,
                                cycle_timestamp=cycle_timestamp
                            )
                        
                        # (Пункт 5) Строгий merge: никогда не перезаписывать
                        self._merge_info(merged_traffic[ip], traffic_info, source_name)
                        
                except Exception as e:
                    logger.error(f"Source '{source_name}' failed: {e}")
                    source.stats["errors"] += 1

            # Логирование статистики (Пункт 12 и 13)
            for source in sources:
                logger.info(
                    f"Traffic {source.get_name().capitalize()}: "
                    f"{source.stats['devices']} devices, "
                    f"{source.stats['elapsed_ms']:.1f} ms, "
                    f"errors: {source.stats['errors']}"
                )
            logger.info(f"Traffic Merged: {len(merged_traffic)} devices")
            
        finally:
            # (Пункт 11) Завершение
            for source in sources:
                source.shutdown()

        return merged_traffic

    def _merge_info(self, target: TrafficInfo, source_info: TrafficInfo, source_name: str):
        """
        (Пункт 5) Инвариант: никогда не перезаписывать существующие данные.
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
                
            # (Пункт 5) Если в target уже есть значение, или в source None — пропускаем
            if getattr(target, key) is not None:
                continue
            if value is None:
                continue
                
            setattr(target, key, value)


traffic_collector = TrafficCollector()
