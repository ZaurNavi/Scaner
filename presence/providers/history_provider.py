#!/usr/bin/env python3
"""History Provider: возвращает ТОЛЬКО сырые данные."""
from typing import Dict, Any
from history import HistoryService

class HistoryProvider:
    name = "history_provider"
    
    def __init__(self, history_service: HistoryService):
        self.history_service = history_service
        
    def extract(self, device_id: str) -> Dict[str, Any]:
        history = self.history_service.get_device_history(device_id)
        
        return {
            "first_seen": history.first_seen.isoformat() if history.first_seen else None,
            "last_seen": history.last_seen.isoformat() if history.last_seen else None,
            "snapshots": [
                {
                    "timestamp": s.timestamp.isoformat(),
                    "ip": s.ip,
                    "hostname": s.hostname
                } for s in history.snapshots
            ],
            "observations_count": len(history.observations),
            "events_count": len(history.events)
        }
