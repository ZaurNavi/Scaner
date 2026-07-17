#!/usr/bin/env python3
"""Profile Snapshot Cache — кэш для Profile."""
from typing import Dict, Optional
from .profile import UnifiedDeviceProfile
from ..cache.platform import VersionSnapshot

class ProfileSnapshotCache:
    """Кэш для UnifiedDeviceProfile."""
    
    def __init__(self):
        self._profiles: Dict[str, UnifiedDeviceProfile] = {}
        self._versions: Dict[str, tuple] = {}
    
    def get(self, device_id: str, version_snapshot: VersionSnapshot) -> Optional[UnifiedDeviceProfile]:
        """Получает Profile из кэша (если версия совпадает)."""
        if device_id not in self._profiles:
            return None
        
        cached_version = self._versions.get(device_id)
        current_version = version_snapshot.to_cache_key()
        
        if cached_version != current_version:
            return None
        
        return self._profiles[device_id]
    
    def put(self, device_id: str, profile: UnifiedDeviceProfile, version_snapshot: VersionSnapshot):
        """Сохраняет Profile в кэш."""
        self._profiles[device_id] = profile
        self._versions[device_id] = version_snapshot.to_cache_key()
    
    def invalidate(self, device_id: str):
        """Инвалидирует кэш для устройства."""
        if device_id in self._profiles:
            del self._profiles[device_id]
        if device_id in self._versions:
            del self._versions[device_id]
    
    def clear(self):
        """Очищает весь кэш."""
        self._profiles.clear()
        self._versions.clear()
