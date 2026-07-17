#!/usr/bin/env python3
"""Knowledge Cache — отдельный кэш для Snapshot'ов."""
from typing import Dict, Optional
from .snapshot import KnowledgeSnapshot

class KnowledgeCache:
    """
    Отдельный кэш для Knowledge Snapshot.
    
    ИСПРАВЛЕНО: вынесен из KnowledgeService, чтобы Service был чистым фасадом.
    """
    
    def __init__(self):
        self._snapshots: Dict[str, KnowledgeSnapshot] = {}
    
    def get(self, device_id: str) -> Optional[KnowledgeSnapshot]:
        """Получает Snapshot из кэша."""
        return self._snapshots.get(device_id)
    
    def put(self, device_id: str, snapshot: KnowledgeSnapshot):
        """Сохраняет Snapshot в кэш."""
        self._snapshots[device_id] = snapshot
    
    def invalidate(self, device_id: str):
        """Инвалидирует кэш для устройства."""
        if device_id in self._snapshots:
            del self._snapshots[device_id]
    
    def clear(self):
        """Очищает весь кэш."""
        self._snapshots.clear()
