#!/usr/bin/env python3
"""Feature Builder: создает ПРИЗНАКИ из метрик (не правила!)."""
from datetime import datetime
from ..models import UsageMetricSet, UsageFeatureSet, UsageFeature
from ..constants import *

class FeatureBuilder:
    """Создает ПРИЗНАКИ из метрик. Все features ВСЕГДА существуют."""
    
    def build(self, metrics: UsageMetricSet) -> UsageFeatureSet:
        """Создает все возможные Features (даже если значение False)."""
        features = {}
        
        # Извлекаем метрики
        total_bytes_metric = metrics.get("total_bytes")
        upload_ratio_metric = metrics.get("upload_ratio")
        download_ratio_metric = metrics.get("download_ratio")
        active_hours_metric = metrics.get("active_hours")
        traffic_density_metric = metrics.get("traffic_density")
        burst_ratio_metric = metrics.get("burst_ratio")
        
        total_bytes = total_bytes_metric.value if total_bytes_metric else 0
        upload_ratio = upload_ratio_metric.value if upload_ratio_metric else 0.0
        download_ratio = download_ratio_metric.value if download_ratio_metric else 0.0
        active_hours = active_hours_metric.value if active_hours_metric else 0.0
        traffic_density = traffic_density_metric.value if traffic_density_metric else 0.0
        burst_ratio = burst_ratio_metric.value if burst_ratio_metric else 0.0
        
        # === Feature: usage_class (классификация) ===
        usage_class = self._classify_usage(total_bytes, active_hours, traffic_density)
        features["usage_class"] = UsageFeature(
            id="usage_class", name="Usage Class", value=usage_class,
            unit="category", version="1.0.0", confidence=85.0,
            quality=total_bytes_metric.quality if total_bytes_metric else None,
            sources=total_bytes_metric.sources if total_bytes_metric else [],
            generated_at=datetime.now(),
            dependencies=["total_bytes", "active_hours", "traffic_density"],
            availability=True, availability_reason="",
            interpretation=f"Класс использования: {usage_class}"
        )
        
        # === Feature: upload_dominant ===
        upload_dominant = upload_ratio > UPLOAD_DOMINANT_THRESHOLD
        features["upload_dominant"] = UsageFeature(
            id="upload_dominant", name="Upload Dominant", value=upload_dominant,
            unit="boolean", version="1.0.0", confidence=85.0,
            quality=upload_ratio_metric.quality if upload_ratio_metric else None,
            sources=upload_ratio_metric.sources if upload_ratio_metric else [],
            generated_at=datetime.now(),
            dependencies=["upload_ratio"],
            availability=True, availability_reason="",
            interpretation=f"Исходящий трафик преобладает: {upload_dominant} ({upload_ratio:.2%})"
        )
        
        # === Feature: download_dominant ===
        download_dominant = download_ratio > DOWNLOAD_DOMINANT_THRESHOLD
        features["download_dominant"] = UsageFeature(
            id="download_dominant", name="Download Dominant", value=download_dominant,
            unit="boolean", version="1.0.0", confidence=85.0,
            quality=download_ratio_metric.quality if download_ratio_metric else None,
            sources=download_ratio_metric.sources if download_ratio_metric else [],
            generated_at=datetime.now(),
            dependencies=["download_ratio"],
            availability=True, availability_reason="",
            interpretation=f"Входящий трафик преобладает: {download_dominant} ({download_ratio:.2%})"
        )
        
        # === Feature: bursty_traffic ===
        bursty_traffic = burst_ratio > BURST_RATIO_THRESHOLD
        features["bursty_traffic"] = UsageFeature(
            id="bursty_traffic", name="Bursty Traffic", value=bursty_traffic,
            unit="boolean", version="1.0.0", confidence=75.0,
            quality=burst_ratio_metric.quality if burst_ratio_metric else None,
            sources=burst_ratio_metric.sources if burst_ratio_metric else [],
            generated_at=datetime.now(),
            dependencies=["burst_ratio"],
            availability=True, availability_reason="",
            interpretation=f"Трафик bursts: {bursty_traffic} ({burst_ratio:.2%})"
        )
        
        # === Feature: active_hours_ratio ===
        active_hours_ratio = min(active_hours / 24.0, 1.0)  # Нормализация к 0..1
        features["active_hours_ratio"] = UsageFeature(
            id="active_hours_ratio", name="Active Hours Ratio", value=active_hours_ratio,
            unit="ratio", version="1.0.0", confidence=80.0,
            quality=active_hours_metric.quality if active_hours_metric else None,
            sources=active_hours_metric.sources if active_hours_metric else [],
            generated_at=datetime.now(),
            dependencies=["active_hours"],
            availability=True, availability_reason="",
            interpretation=f"Доля активных часов: {active_hours_ratio:.2%}"
        )
        
        # === Feature: traffic_density ===
        features["traffic_density"] = UsageFeature(
            id="traffic_density", name="Traffic Density", value=traffic_density,
            unit="bytes/sec", version="1.0.0", confidence=75.0,
            quality=traffic_density_metric.quality if traffic_density_metric else None,
            sources=traffic_density_metric.sources if traffic_density_metric else [],
            generated_at=datetime.now(),
            dependencies=["traffic_density"],
            availability=True, availability_reason="",
            interpretation=f"Плотность трафика: {traffic_density:.2f} bytes/sec"
        )
        
        return features
    
    def _classify_usage(self, total_bytes: int, active_hours: float, traffic_density: float) -> str:
        """Классифицирует usage на основе признаков (не правил!)."""
        # Background: низкая активность и малый трафик
        if active_hours < BACKGROUND_HOURS_THRESHOLD and total_bytes < BACKGROUND_USAGE_THRESHOLD:
            return "background"
        
        # Heavy: большой трафик
        if total_bytes > HEAVY_USAGE_THRESHOLD:
            return "heavy"
        
        # Persistent: длительная активность с высокой плотностью
        if active_hours > PERSISTENT_HOURS_THRESHOLD and traffic_density > PERSISTENT_DENSITY_THRESHOLD:
            return "persistent"
        
        # Light: малый трафик
        if total_bytes < LIGHT_USAGE_THRESHOLD:
            return "light"
        
        # Normal: всё остальное
        return "normal"
