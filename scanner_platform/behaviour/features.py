#!/usr/bin/env python3
"""
FeatureBuilder — вычисление СЫРЫХ признаков поведения.
DerivedFeatureCalculator — вычисление ПРОИЗВОДНЫХ признаков.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from .models import FeatureSet
from history import HistoryService
from identity import IdentityService
from session import SessionEngine


class FeatureBuilder:
    """Вычисляет СЫРЫЕ признаки поведения из публичных сервисов."""
    
    def __init__(
        self,
        history_service: HistoryService,
        identity_service: IdentityService,
        session_engine: Optional[SessionEngine] = None
    ):
        self.history = history_service
        self.identity = identity_service
        self.session = session_engine
    
    def build(self, device_id: str) -> FeatureSet:
        """
        Вычисляет сырые признаки для устройства.
        Производные признаки вычисляются в DerivedFeatureCalculator.
        """
        features = FeatureSet(generated_at=datetime.now())
        
        # Получаем Identity
        identity_profile = self.identity.get_identity(device_id)
        if not identity_profile:
            return features
        
        # Время жизни
        features.first_seen = identity_profile.timeline.first_seen
        features.last_seen = identity_profile.timeline.last_seen
        
        # Мобильность (из Identity)
        features.ap_changes = len(identity_profile.network.known_aps)
        features.ssid_changes = len(identity_profile.network.known_ssids)
        
        # Сессии (из Session Engine, если доступен)
        if self.session:
            active_session = self.session.get_active_session(device_id)
            if active_session:
                features.session_count = 1
                features.total_session_duration = active_session.duration or 0
        
        # Трафик (из Identity statistics)
        features.total_traffic = identity_profile.traffic_statistics.total_traffic
        features.total_download = identity_profile.traffic_statistics.total_download
        features.total_upload = identity_profile.traffic_statistics.total_upload
        
        return features


class DerivedFeatureCalculator:
    """Вычисляет ПРОИЗВОДНЫЕ признаки на основе сырых."""
    
    def calculate(self, features: FeatureSet) -> FeatureSet:
        """Вычисляет производные признаки."""
        # Время жизни
        if features.first_seen and features.last_seen:
            features.lifetime_seconds = (features.last_seen - features.first_seen).total_seconds()
        
        # Средняя длительность сессии
        if features.session_count > 0:
            features.average_session_duration = features.total_session_duration / features.session_count
        
        # Активность
        if features.lifetime_seconds and features.lifetime_seconds > 0:
            active_time = features.total_session_duration
            features.active_ratio = active_time / features.lifetime_seconds
            features.idle_ratio = 1.0 - features.active_ratio
        
        # Скорость
        if features.lifetime_seconds and features.lifetime_seconds > 0 and features.total_traffic > 0:
            features.average_speed = (features.total_traffic * 8) / (features.lifetime_seconds * 1_000_000)
            features.peak_speed = features.average_speed * 2
        
        return features
