#!/usr/bin/env python3
"""Пример Provider, извлекающего сырые метрики из Session Service."""
from typing import Dict, Any
from session import SessionEngine

class SessionMetricsProvider:
    name = "session_provider"
    
    def __init__(self, session_engine: SessionEngine):
        self.session_engine = session_engine
        
    def extract(self, device_id: str) -> Dict[str, Any]:
        metrics = {}
        session = self.session_engine.get_active_session(device_id)
        if session:
            metrics["session_count"] = 1 # Упрощено для примера
            metrics["unique_ap_count"] = len(set([s.get("ap") for s in session.timeline if s.get("ap")])) # Псевдокод
        else:
            metrics["session_count"] = 0
            metrics["unique_ap_count"] = 0
        return metrics
