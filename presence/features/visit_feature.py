#!/usr/bin/env python3
"""Feature Builder: вычисляет Presence Features из Metrics (авто-регистрация)."""
from datetime import datetime
from ..registry import register_feature
from ..models import PresenceFeature, Availability

@register_feature("history_depth_days")
def build_history_depth_days(metrics: dict) -> PresenceFeature:
    metric = metrics.get("history_depth_days")
    if not metric:
        return PresenceFeature(
            id="history_depth_days", name="History Depth", value=0,
            availability=Availability(available=False, reason="Metric unavailable")
        )
    
    return PresenceFeature(
        id="history_depth_days",
        name="History Depth (Days)",
        value=metric.value,
        unit=metric.unit,
        confidence=metric.confidence,
        coverage=metric.quality.coverage,
        samples=metric.quality.samples,
        sources=metric.sources,
        generated_at=datetime.now(),
        dependencies=[],
        availability=Availability(available=True, reason="")
    )

@register_feature("visit_count")
def build_visit_count(metrics: dict) -> PresenceFeature:
    metric = metrics.get("visit_count")
    if not metric:
        return PresenceFeature(
            id="visit_count", name="Visit Count", value=0,
            availability=Availability(available=False, reason="Metric unavailable")
        )
    
    return PresenceFeature(
        id="visit_count",
        name="Visit Count",
        value=metric.value,
        unit=metric.unit,
        confidence=metric.confidence,
        coverage=metric.quality.coverage,
        samples=metric.quality.samples,
        sources=metric.sources,
        generated_at=datetime.now(),
        dependencies=["history_depth_days"],
        availability=Availability(available=True, reason="")
    )

@register_feature("active_days_ratio")
def build_active_days_ratio(metrics: dict) -> PresenceFeature:
    metric = metrics.get("active_days_ratio")
    if not metric:
        return PresenceFeature(
            id="active_days_ratio", name="Active Days Ratio", value=0.0,
            availability=Availability(available=False, reason="Metric unavailable")
        )
    
    return PresenceFeature(
        id="active_days_ratio",
        name="Active Days Ratio",
        value=metric.value,
        unit=metric.unit,
        confidence=metric.confidence,
        coverage=metric.quality.coverage,
        samples=metric.quality.samples,
        sources=metric.sources,
        generated_at=datetime.now(),
        dependencies=["visit_count", "history_depth_days"],
        availability=Availability(available=True, reason="")
    )

@register_feature("night_activity_ratio")
def build_night_activity_ratio(metrics: dict) -> PresenceFeature:
    metric = metrics.get("night_activity_ratio")
    if not metric:
        return PresenceFeature(
            id="night_activity_ratio", name="Night Activity Ratio", value=0.0,
            availability=Availability(available=False, reason="Metric unavailable")
        )
    
    return PresenceFeature(
        id="night_activity_ratio",
        name="Night Activity Ratio",
        value=metric.value,
        unit=metric.unit,
        confidence=metric.confidence,
        coverage=metric.quality.coverage,
        samples=metric.quality.samples,
        sources=metric.sources,
        generated_at=datetime.now(),
        dependencies=["visit_count"],
        availability=Availability(available=True, reason="")
    )

@register_feature("weekend_activity_ratio")
def build_weekend_activity_ratio(metrics: dict) -> PresenceFeature:
    metric = metrics.get("weekend_activity_ratio")
    if not metric:
        return PresenceFeature(
            id="weekend_activity_ratio", name="Weekend Activity Ratio", value=0.0,
            availability=Availability(available=False, reason="Metric unavailable")
        )
    
    return PresenceFeature(
        id="weekend_activity_ratio",
        name="Weekend Activity Ratio",
        value=metric.value,
        unit=metric.unit,
        confidence=metric.confidence,
        coverage=metric.quality.coverage,
        samples=metric.quality.samples,
        sources=metric.sources,
        generated_at=datetime.now(),
        dependencies=["visit_count"],
        availability=Availability(available=True, reason="")
    )

@register_feature("business_hours_ratio")
def build_business_hours_ratio(metrics: dict) -> PresenceFeature:
    metric = metrics.get("business_hours_ratio")
    if not metric:
        return PresenceFeature(
            id="business_hours_ratio", name="Business Hours Ratio", value=0.0,
            availability=Availability(available=False, reason="Metric unavailable")
        )
    
    return PresenceFeature(
        id="business_hours_ratio",
        name="Business Hours Ratio",
        value=metric.value,
        unit=metric.unit,
        confidence=metric.confidence,
        coverage=metric.quality.coverage,
        samples=metric.quality.samples,
        sources=metric.sources,
        generated_at=datetime.now(),
        dependencies=["visit_count"],
        availability=Availability(available=True, reason="")
    )
