#!/usr/bin/env python3
"""Пример Feature Builder."""
from datetime import datetime
from .registry import FeatureRegistry
from ..models import MobilityFeature, DataQuality, Availability

def build_roaming_rate(metrics: dict) -> MobilityFeature:
    # Пример вычисления на основе сырых метрик
    ap_changes = metrics.get("unique_ap_count", 0)
    sessions = max(metrics.get("session_count", 1), 1)
    rate = ap_changes / sessions
    
    availability = Availability(available=True, reason="") if ap_changes >= 0 else Availability(available=False, reason="No AP history")
    
    return MobilityFeature(
        id="roaming_rate",
        name="Roaming Rate",
        value=rate,
        unit="APs/session",
        confidence=0.8,
        data_quality=DataQuality(samples=sessions, confidence=0.8),
        availability=availability,
        sources=["session_provider"],
        generated_at=datetime.now(),
        dependencies=["unique_ap_count", "session_count"]
    )

# Регистрация в Feature Registry
from .registry import FeatureRegistry
FeatureRegistry.register("roaming_rate", build_roaming_rate)
