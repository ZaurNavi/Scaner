#!/usr/bin/env python3
"""Metrics Builder: вычисляет метрики из сырых данных (Замечание №1)."""
from datetime import datetime
from typing import Dict, Any
from ..models import PresenceMetric, PresenceQuality, Availability
from ..constants import BUSINESS_HOURS_START, BUSINESS_HOURS_END, NIGHT_HOURS_START, NIGHT_HOURS_END

class MetricsBuilder:
    """Вычисляет Presence Metrics из сырых данных Providers."""
    
    def build(self, raw_data: dict) -> Dict[str, PresenceMetric]:
        metrics = {}
        
        snapshots = raw_data.get("snapshots", [])
        first_seen = raw_data.get("first_seen")
        last_seen = raw_data.get("last_seen")
        
        # history_depth_days
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
            confidence=0.95,
            quality=PresenceQuality(coverage=1.0, samples=1, history_depth=history_depth, confidence=0.95),
            availability=Availability(available=True, reason=""),
            sources=["history_provider"],
            generated_at=datetime.now()
        )
        
        # visit_count (уникальные дни)
        unique_days = set()
        hour_distribution = {}
        weekday_distribution = {}
        
        for snap in snapshots:
            ts = snap.get("timestamp")
            if ts:
                dt = datetime.fromisoformat(ts)
                unique_days.add(dt.date())
                hour_distribution[dt.hour] = hour_distribution.get(dt.hour, 0) + 1
                weekday_distribution[dt.weekday()] = weekday_distribution.get(dt.weekday(), 0) + 1
        
        visit_count = len(unique_days)
        
        metrics["visit_count"] = PresenceMetric(
            id="visit_count",
            name="Visit Count",
            value=visit_count,
            unit="visits",
            confidence=0.9,
            quality=PresenceQuality(coverage=1.0, samples=visit_count, history_depth=history_depth, confidence=0.9),
            availability=Availability(available=True, reason=""),
            sources=["history_provider"],
            generated_at=datetime.now()
        )
        
        # active_days_ratio
        active_days_ratio = visit_count / max(history_depth, 1)
        metrics["active_days_ratio"] = PresenceMetric(
            id="active_days_ratio",
            name="Active Days Ratio",
            value=active_days_ratio,
            unit="ratio",
            confidence=0.85,
            quality=PresenceQuality(coverage=0.9, samples=visit_count, history_depth=history_depth, confidence=0.85),
            availability=Availability(available=True, reason=""),
            sources=["history_provider"],
            generated_at=datetime.now()
        )
        
        # Distribution metrics
        total_hours = sum(hour_distribution.values())
        total_days = sum(weekday_distribution.values())
        
        # night_activity_ratio
        night_hours = sum(hour_distribution.get(h, 0) for h in list(range(0, NIGHT_HOURS_END)) + list(range(NIGHT_HOURS_START, 24)))
        night_activity_ratio = night_hours / total_hours if total_hours > 0 else 0.0
        
        metrics["night_activity_ratio"] = PresenceMetric(
            id="night_activity_ratio",
            name="Night Activity Ratio",
            value=night_activity_ratio,
            unit="ratio",
            confidence=0.8,
            quality=PresenceQuality(coverage=0.8, samples=total_hours, history_depth=history_depth, confidence=0.8),
            availability=Availability(available=True, reason=""),
            sources=["history_provider"],
            generated_at=datetime.now()
        )
        
        # weekend_activity_ratio
        weekend_days = sum(weekday_distribution.get(d, 0) for d in [5, 6])
        weekend_activity_ratio = weekend_days / total_days if total_days > 0 else 0.0
        
        metrics["weekend_activity_ratio"] = PresenceMetric(
            id="weekend_activity_ratio",
            name="Weekend Activity Ratio",
            value=weekend_activity_ratio,
            unit="ratio",
            confidence=0.8,
            quality=PresenceQuality(coverage=0.8, samples=total_days, history_depth=history_depth, confidence=0.8),
            availability=Availability(available=True, reason=""),
            sources=["history_provider"],
            generated_at=datetime.now()
        )
        
        # business_hours_ratio
        business_hours = sum(hour_distribution.get(h, 0) for h in range(BUSINESS_HOURS_START, BUSINESS_HOURS_END))
        business_hours_ratio = business_hours / total_hours if total_hours > 0 else 0.0
        
        metrics["business_hours_ratio"] = PresenceMetric(
            id="business_hours_ratio",
            name="Business Hours Ratio",
            value=business_hours_ratio,
            unit="ratio",
            confidence=0.8,
            quality=PresenceQuality(coverage=0.8, samples=total_hours, history_depth=history_depth, confidence=0.8),
            availability=Availability(available=True, reason=""),
            sources=["history_provider"],
            generated_at=datetime.now()
        )
        
        return metrics
