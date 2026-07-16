#!/usr/bin/env python3
"""Traffic Provider: возвращает ТОЛЬКО сырые события."""
from typing import List, Dict, Any
from history import HistoryService
from ..models import TrafficEvent, ProviderQuality
from datetime import datetime

class TrafficProvider:
    name = "traffic_provider"
    
    def __init__(self, history_service: HistoryService):
        self.history_service = history_service
        
    def extract(self, device_id: str) -> Dict[str, Any]:
        """Возвращает сырые события трафика + оценку качества."""
        history = self.history_service.get_device_history(device_id)
        
        traffic_events: List[TrafficEvent] = []
        
        for obs in history.observations:
            if hasattr(obs, 'observation_type') and obs.observation_type == 'traffic':
                data = obs.data if hasattr(obs, 'data') else {}
                event = TrafficEvent(
                    timestamp=obs.timestamp if hasattr(obs, 'timestamp') else datetime.now(),
                    download_bytes=data.get('download', 0),
                    upload_bytes=data.get('upload', 0),
                    flow_count=data.get('flows', 0),
                    session_id=data.get('session_id'),
                    source="traffic_provider"
                )
                traffic_events.append(event)
        
        quality = ProviderQuality(
            provider="traffic_provider",
            coverage=1.0 if traffic_events else 0.0,
            freshness=1.0,
            availability=1.0 if traffic_events else 0.0,  # float, не bool
            latency_ms=0.0,
            errors=0,
            generated_at=datetime.now(),
            version="1.0.0"
        )
        
        return {
            "traffic_events": traffic_events,
            "provider_quality": quality
        }
