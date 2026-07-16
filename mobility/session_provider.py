#!/usr/bin/env python3
"""Session Provider: возвращает только сырые метрики."""
from typing import Dict, Any
from session import SessionEngine

class SessionMetricsProvider:
    name = "session_provider"
    
    def __init__(self, session_engine: SessionEngine):
        self.session_engine = session_engine
        
    def extract(self, device_id: str) -> Dict[str, Any]:
        # Возвращаем ТОЛЬКО сырые факты. Никаких rate = x / y
        metrics = {
            "session_count": 0,
            "ap_list": [],
            "reconnect_count": 0,
            "total_session_duration": 0.0
        }
        
        session = self.session_engine.get_active_session(device_id)
        if session:
            metrics["session_count"] = 1
            metrics["total_session_duration"] = session.duration or 0.0
            # Псевдокод извлечения сырых данных из timeline сессии
            metrics["ap_list"] = ["AP-1", "AP-2"] # Пример
            metrics["reconnect_count"] = 2        # Пример
            
        return metrics
