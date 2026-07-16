#!/usr/bin/env python3
"""Absolute Metrics Builder (Замечание №12: разделён)."""
from datetime import datetime
from typing import Dict
from ..models import PresenceMetric, PresenceQuality, Availability

def build_absolute_metrics(raw_data: dict) -> Dict[str, PresenceMetric]:
    """Вычисляет абсолютные метрики."""
    metrics = {}
    
    snapshots = raw_data.get("snapshots", [])
    first_seen = raw_data.get("first_seen")
    last_seen = raw_data.get("last_seen")
    
    if first_seen and last_seen:
        first_dt = datetime.fromisoformat(first_seen)
        last_dt = datetime.fromisoformat(last_seen)
        history_depth = (last_dt - first_dt).days
    else:
        history_depth = 0
    
    metrics["history_depth_days"] = PresenceMetric(
        id="history_depth_days",
        name="History Depth",
        value=history_depth,
        unit="days",
        version="1.0.0",
        confidence=0.95,
        quality=PresenceQuality(coverage=1.0, samples=1, history_depth=history_depth, freshness=1.0, confidence=0.95),
        availability=Availability(available=True, reason=""),
        sources=["history_provider"],
        generated_at=datetime.now()
    )
    
    unique_days = set()
    for snap in snapshots:
        ts = snap.get("timestamp")
        if ts:
            dt = datetime.fromisoformat(ts)
            unique_days.add(dt.date())
    
    visit_count = len(unique_days)
    
    metrics["visit_count"] = PresenceMetric(
        id="visit_count",
        name="Visit Count",
        value=visit_count,
        unit="visits",
        version="1.0.0",
        confidence=0.9,
        quality=PresenceQuality(coverage=1.0, samples=visit_count, history_depth=history_depth, freshness=1.0, confidence=0.9),
        availability=Availability(available=True, reason=""),
        sources=["history_provider"],
        generated_at=datetime.now()
    )
    
    active_days_ratio = visit_count / max(history_depth, 1)
    metrics["active_days_ratio"] = PresenceMetric(
        id="active_days_ratio",
        name="Active Days Ratio",
        value=active_days_ratio,
        unit="ratio",
        version="1.0.0",
        confidence=0.85,
        quality=PresenceQuality(coverage=0.9, samples=visit_count, history_depth=history_depth, freshness=1.0, confidence=0.85),
        availability=Availability(available=True, reason=""),
        sources=["history_provider"],
        generated_at=datetime.now()
    )
    
    return metrics
