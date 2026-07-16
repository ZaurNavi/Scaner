#!/usr/bin/env python3
"""Константы и версии для Usage Engine."""

# Версии
ENGINE_VERSION = "1.0.0"
RULES_VERSION = "1.0.0"
FEATURE_VERSION = "1.0.0"
PROVIDER_VERSION = "1.0.0"
METRICS_VERSION = "1.0.0"
TIMELINE_VERSION = "1.0.0"

# Analysis Windows (в днях)
ANALYSIS_WINDOWS = {
    "last_session": 0,
    "today": 1,
    "7_days": 7,
    "30_days": 30,
    "90_days": 90,
    "all_time": -1
}

# Пороги для классификации usage_class
HEAVY_USAGE_THRESHOLD = 500 * 1024 * 1024  # 500 MB
LIGHT_USAGE_THRESHOLD = 10 * 1024 * 1024   # 10 MB
BACKGROUND_USAGE_THRESHOLD = 50 * 1024 * 1024  # 50 MB
BACKGROUND_HOURS_THRESHOLD = 2  # часа
PERSISTENT_HOURS_THRESHOLD = 12  # часа
PERSISTENT_DENSITY_THRESHOLD = 1000  # bytes/sec
BURST_RATIO_THRESHOLD = 0.3  # 30%
UPLOAD_DOMINANT_THRESHOLD = 0.7  # 70%
DOWNLOAD_DOMINANT_THRESHOLD = 0.7  # 70%
