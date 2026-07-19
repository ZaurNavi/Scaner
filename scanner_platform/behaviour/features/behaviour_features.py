#!/usr/bin/env python3
"""Feature Builders для Behaviour Engine."""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# v1.6.9.2: ИСПРАВЛЕНО — FeatureSet находится в ../models.py, а не в ./models.py
from ..models import FeatureSet

from history import HistoryService
from identity import IdentityService
from session import SessionEngine


class FeatureBuilder:
    """
    Строит FeatureSet из истории, identity и сессий устройства.
    
    v1.6.9.2: Принимает сервисы через конструктор (Dependency Injection).
    """
    
    def __init__(
        self,
        history_service: HistoryService,
        identity_service: IdentityService,
        session_engine: Optional[SessionEngine] = None
    ):
        self.history_service = history_service
        self.identity_service = identity_service
        self.session_engine = session_engine
    
    def build(self, device_id: str) -> FeatureSet:
        """
        Строит FeatureSet для устройства.
        
        Args:
            device_id: UUID устройства
        
        Returns:
            FeatureSet с вычисленными признаками
        """
        features = FeatureSet(generated_at=datetime.now())
        
        try:
            # === 1. Получаем историю устройства ===
            device_history = self.history_service.get_device_history(device_id)
            
            if device_history:
                # Lifetime
                if hasattr(device_history, 'first_seen') and device_history.first_seen:
                    lifetime = (datetime.now() - device_history.first_seen).total_seconds()
                    features.lifetime_seconds = lifetime
                
                # AP/SSID changes
                if hasattr(device_history, 'observations'):
                    ap_set = set()
                    ssid_set = set()
                    for obs in device_history.observations:
                        if hasattr(obs, 'ap_mac') and obs.ap_mac:
                            ap_set.add(obs.ap_mac)
                        if hasattr(obs, 'ssid') and obs.ssid:
                            ssid_set.add(obs.ssid)
                    features.ap_changes = len(ap_set)
                    features.ssid_changes = len(ssid_set)
                
                # Snapshots для вычисления паттернов
                if hasattr(device_history, 'snapshots'):
                    self._compute_presence_features(features, device_history.snapshots)
            
            # === 2. Получаем сессии ===
            if self.session_engine:
                try:
                    sessions = self.session_engine.get_sessions(device_id)
                    if sessions:
                        self._compute_session_features(features, sessions)
                except Exception:
                    pass  # Сессии могут быть недоступны
            
            # === 3. Получаем identity (для трафика) ===
            if self.identity_service:
                try:
                    identity = self.identity_service.get_identity(device_id)
                    if identity and hasattr(identity, 'traffic_stats'):
                        self._compute_traffic_features(features, identity.traffic_stats)
                except Exception:
                    pass  # Identity может быть недоступна
        
        except Exception as e:
            # Если что-то пошло не так — возвращаем пустой FeatureSet
            pass
        
        return features
    
    def _compute_presence_features(self, features: FeatureSet, snapshots: list):
        """Вычисляет признаки присутствия из snapshots."""
        if not snapshots:
            return
        
        now = datetime.now()
        total_days = 0
        active_days = 0
        night_days = 0
        weekend_days = 0
        weekday_days = 0
        office_days = 0
        
        for snap in snapshots:
            if not hasattr(snap, 'timestamp'):
                continue
            
            snap_time = snap.timestamp
            total_days += 1
            
            # Active day
            active_days += 1
            
            # Night (22:00 - 06:00)
            if snap_time.hour >= 22 or snap_time.hour < 6:
                night_days += 1
            
            # Weekend (Saturday=5, Sunday=6)
            if snap_time.weekday() >= 5:
                weekend_days += 1
            else:
                weekday_days += 1
            
            # Office hours (09:00 - 18:00)
            if 9 <= snap_time.hour < 18:
                office_days += 1
        
        # Вычисляем ratios и сохраняем в features._metrics
        if total_days > 0:
            features._metrics = {
                'daily_presence': active_days / max(total_days, 1),
                'night_activity': night_days / max(total_days, 1),
                'weekend_presence': weekend_days / max(total_days, 1),
                'weekday_ratio': weekday_days / max(total_days, 1),
                'office_hours_activity': office_days / max(total_days, 1),
                'appearance_frequency': len(snapshots),
                'idle_duration': 0.0,
                'online_duration': 0.0,
                'weekly_presence': active_days / 7.0,
            }
    
    def _compute_session_features(self, features: FeatureSet, sessions: list):
        """Вычисляет признаки из сессий."""
        if not sessions:
            return
        
        features.session_count = len(sessions)
        
        total_duration = 0.0
        for session in sessions:
            if hasattr(session, 'duration') and session.duration:
                total_duration += session.duration
        
        features.total_session_duration = total_duration
        if features.session_count > 0:
            features.average_session_duration = total_duration / features.session_count
    
    def _compute_traffic_features(self, features: FeatureSet, traffic_stats: dict):
        """Вычисляет признаки из трафика."""
        if not traffic_stats:
            return
        
        features.total_traffic = traffic_stats.get('total_bytes', 0)
        features.peak_speed = traffic_stats.get('peak_speed')
        features.average_speed = traffic_stats.get('average_speed')
        
        total_time = traffic_stats.get('total_time', 0)
        active_time = traffic_stats.get('active_time', 0)
        
        if total_time > 0:
            features.active_ratio = active_time / total_time
            features.idle_ratio = 1.0 - features.active_ratio


# === Legacy функции (для обратной совместимости) ===

def build_regular_schedule(metrics: Dict[str, Any]) -> bool:
    """Устройство появляется по регулярному расписанию."""
    daily = metrics.get("daily_presence", 0.0)
    weekday = metrics.get("weekday_ratio", 0.0)
    office = metrics.get("office_hours_activity", 0.0)
    return daily > 0.5 and weekday > 0.7 and office > 0.6

def build_night_user(metrics: Dict[str, Any]) -> bool:
    """Устройство активно ночью."""
    night = metrics.get("night_activity", 0.0)
    return night > 0.3

def build_weekend_device(metrics: Dict[str, Any]) -> bool:
    """Устройство активно в выходные."""
    weekend = metrics.get("weekend_presence", 0.0)
    return weekend > 0.4

def build_office_pattern(metrics: Dict[str, Any]) -> bool:
    """Паттерн офисного устройства."""
    office = metrics.get("office_hours_activity", 0.0)
    weekday = metrics.get("weekday_ratio", 0.0)
    return office > 0.6 and weekday > 0.7

def build_home_pattern(metrics: Dict[str, Any]) -> bool:
    """Паттерн домашнего устройства."""
    weekend = metrics.get("weekend_presence", 0.0)
    night = metrics.get("night_activity", 0.0)
    return weekend > 0.3 and night > 0.2

def build_frequent_short_sessions(metrics: Dict[str, Any]) -> bool:
    """Частые короткие сессии."""
    freq = metrics.get("appearance_frequency", 0)
    idle = metrics.get("idle_duration", 0.0)
    return freq > 10 and idle > 0.7

def build_long_sessions(metrics: Dict[str, Any]) -> bool:
    """Длинные сессии."""
    online = metrics.get("online_duration", 0.0)
    return online > 3600  # более 1 часа

def build_irregular_usage(metrics: Dict[str, Any]) -> bool:
    """Нерегулярное использование."""
    daily = metrics.get("daily_presence", 0.0)
    weekly = metrics.get("weekly_presence", 0.0)
    return daily < 0.3 and weekly > 0.2

def build_rare_device(metrics: Dict[str, Any]) -> bool:
    """Редко появляющееся устройство."""
    freq = metrics.get("appearance_frequency", 0)
    daily = metrics.get("daily_presence", 0.0)
    return freq < 3 and daily < 0.1

def build_always_online(metrics: Dict[str, Any]) -> bool:
    """Постоянно онлайн."""
    daily = metrics.get("daily_presence", 0.0)
    idle = metrics.get("idle_duration", 0.0)
    return daily > 0.9 and idle < 0.2

def build_frequently_returning(metrics: Dict[str, Any]) -> bool:
    """Часто возвращающееся устройство."""
    freq = metrics.get("appearance_frequency", 0)
    weekly = metrics.get("weekly_presence", 0.0)
    return freq > 5 and weekly > 0.5
