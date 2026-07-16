#!/usr/bin/env python3
"""Metrics Builder: вычисляет ВСЕ метрики из Timeline (расширенный)."""
from datetime import datetime
from typing import Dict, List
from ..models import Timeline, TimelineEvent, UsageMetricSet, UsageMetric, ProviderQuality
from ..categories import EventType

class MetricsBuilder:
    """Вычисляет ВСЕ метрики из Timeline."""
    
    def build(self, timeline: Timeline, provider_quality: ProviderQuality = None) -> UsageMetricSet:
        """Вычисляет все метрики из Timeline."""
        metrics = {}
        traffic_events = timeline.get_by_type(EventType.TRAFFIC_SAMPLE)
        
        # === Absolute Metrics ===
        total_download = sum(e.payload.get('download_bytes', 0) for e in traffic_events)
        total_upload = sum(e.payload.get('upload_bytes', 0) for e in traffic_events)
        total_bytes = total_download + total_upload
        flow_count = sum(e.payload.get('flow_count', 0) for e in traffic_events)
        
        metrics["total_download"] = UsageMetric(
            id="total_download", name="Total Download", value=total_download,
            unit="bytes", metric_version="1.0.0", confidence=90.0,
            quality=provider_quality, sources=["traffic_provider"],
            generated_at=datetime.now()
        )
        
        metrics["total_upload"] = UsageMetric(
            id="total_upload", name="Total Upload", value=total_upload,
            unit="bytes", metric_version="1.0.0", confidence=90.0,
            quality=provider_quality, sources=["traffic_provider"],
            generated_at=datetime.now()
        )
        
        metrics["total_bytes"] = UsageMetric(
            id="total_bytes", name="Total Bytes", value=total_bytes,
            unit="bytes", metric_version="1.0.0", confidence=90.0,
            quality=provider_quality, sources=["traffic_provider"],
            generated_at=datetime.now()
        )
        
        metrics["flow_count"] = UsageMetric(
            id="flow_count", name="Flow Count", value=flow_count,
            unit="flows", metric_version="1.0.0", confidence=90.0,
            quality=provider_quality, sources=["traffic_provider"],
            generated_at=datetime.now()
        )
        
        # === Rate Metrics ===
        if total_bytes > 0:
            upload_ratio = total_upload / total_bytes
            download_ratio = total_download / total_bytes
        else:
            upload_ratio = 0.0
            download_ratio = 0.0
        
        metrics["upload_ratio"] = UsageMetric(
            id="upload_ratio", name="Upload Ratio", value=upload_ratio,
            unit="ratio", metric_version="1.0.0", confidence=85.0,
            quality=provider_quality, sources=["traffic_provider"],
            generated_at=datetime.now()
        )
        
        metrics["download_ratio"] = UsageMetric(
            id="download_ratio", name="Download Ratio", value=download_ratio,
            unit="ratio", metric_version="1.0.0", confidence=85.0,
            quality=provider_quality, sources=["traffic_provider"],
            generated_at=datetime.now()
        )
        
        # === Peak Metrics ===
        if traffic_events:
            peak_download = max(e.payload.get('download_bytes', 0) for e in traffic_events)
            peak_upload = max(e.payload.get('upload_bytes', 0) for e in traffic_events)
        else:
            peak_download = 0
            peak_upload = 0
        
        metrics["peak_download"] = UsageMetric(
            id="peak_download", name="Peak Download", value=peak_download,
            unit="bytes", metric_version="1.0.0", confidence=80.0,
            quality=provider_quality, sources=["traffic_provider"],
            generated_at=datetime.now()
        )
        
        metrics["peak_upload"] = UsageMetric(
            id="peak_upload", name="Peak Upload", value=peak_upload,
            unit="bytes", metric_version="1.0.0", confidence=80.0,
            quality=provider_quality, sources=["traffic_provider"],
            generated_at=datetime.now()
        )
        
        # === Activity Metrics ===
        if traffic_events:
            first_event = min(e.timestamp for e in traffic_events)
            last_event = max(e.timestamp for e in traffic_events)
            active_hours = (last_event - first_event).total_seconds() / 3600
        else:
            active_hours = 0.0
        
        metrics["active_hours"] = UsageMetric(
            id="active_hours", name="Active Hours", value=active_hours,
            unit="hours", metric_version="1.0.0", confidence=80.0,
            quality=provider_quality, sources=["traffic_provider"],
            generated_at=datetime.now()
        )
        
        # === Burst Metrics ===
        if len(traffic_events) > 1:
            bytes_per_event = [e.payload.get('download_bytes', 0) + e.payload.get('upload_bytes', 0) for e in traffic_events]
            avg_bytes = sum(bytes_per_event) / len(bytes_per_event)
            burst_count = sum(1 for b in bytes_per_event if b > avg_bytes * 2)
            burst_ratio = burst_count / len(traffic_events)
        else:
            burst_ratio = 0.0
        
        metrics["burst_ratio"] = UsageMetric(
            id="burst_ratio", name="Burst Ratio", value=burst_ratio,
            unit="ratio", metric_version="1.0.0", confidence=70.0,
            quality=provider_quality, sources=["traffic_provider"],
            generated_at=datetime.now()
        )
        
        # === Traffic Density ===
        if active_hours > 0:
            traffic_density = total_bytes / (active_hours * 3600)
        else:
            traffic_density = 0.0
        
        metrics["traffic_density"] = UsageMetric(
            id="traffic_density", name="Traffic Density", value=traffic_density,
            unit="bytes/sec", metric_version="1.0.0", confidence=75.0,
            quality=provider_quality, sources=["traffic_provider"],
            generated_at=datetime.now()
        )
        
        total_coverage = sum(m.confidence for m in metrics.values()) / len(metrics) if metrics else 0.0
        
        return UsageMetricSet(
            metrics=metrics,
            generated_at=datetime.now(),
            coverage=total_coverage,
            provider_quality={"traffic_provider": provider_quality} if provider_quality else {}
        )
