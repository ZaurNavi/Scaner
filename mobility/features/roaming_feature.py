#!/usr/bin/env python3
"""Feature Builder: вычисляет признаки из сырых метрик."""
from datetime import datetime
from ..registry import register_feature
from ..models import MobilityFeature, DataQuality, Availability

@register_feature("roaming_rate") # <-- АВТО-РЕГИСТРАЦИЯ
def build_roaming_rate(metrics: dict) -> MobilityFeature:
    sessions = max(metrics.get("session_count", 1), 1)
    reconnects = metrics.get("reconnect_count", 0)
    
    # Вычисление происходит ЗДЕСЬ, а не в Provider
    rate = reconnects / sessions 
    
    availability = Availability(
        available=True, 
        reason=""
    ) if sessions > 0 else Availability(available=False, reason="No session data")
    
    return MobilityFeature(
        id="roaming_rate",
        name="Roaming Rate",
        value=rate,
        unit="reconnects/session",
        confidence=0.8,
        data_quality=DataQuality(samples=sessions, confidence=0.8),
        availability=availability,
        sources=["session_provider"],
        generated_at=datetime.now(),
        dependencies=["session_count", "reconnect_count"]
    )
