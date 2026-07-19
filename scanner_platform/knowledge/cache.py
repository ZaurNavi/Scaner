#!/usr/bin/env python3
"""Knowledge Cache — отдельный кэш для Snapshot'ов.

v1.6.9.8: Интеграция с Configuration Layer.
Кэш теперь имеет лимит размера через DI.
"""
from typing import Dict, Optional
from collections import OrderedDict
from .snapshot import KnowledgeSnapshot

# v1.6.9.8: Configuration Layer Integration
from configuration import ConfigurationManager


class KnowledgeCache:
    """
    Отдельный кэш для Knowledge Snapshot.

    v1.6.9.8: Принимает ConfigurationManager через конструктор (Dependency Injection).
    Использует OrderedDict для LRU- eviction.
    """

    def __init__(
        self,
        configuration: Optional[ConfigurationManager] = None,
        max_size: Optional[int] = None
    ):
        """
        v1.6.9.8: Конструктор с Dependency Injection.
        
        Args:
            configuration: ConfigurationManager (опционально)
            max_size: Максимальный размер кэша (переопределяет configuration)
        """
        # v1.6.9.8: Получаем max_size из configuration или используем дефолт
        if max_size is not None:
            self._max_size = max_size
        elif configuration is not None:
            self._max_size = configuration.get("knowledge.cache_size", 10000)
        else:
            self._max_size = 10000  # Fallback
        
        # v1.6.9.8: Используем OrderedDict для LRU eviction
        self._snapshots: OrderedDict[str, KnowledgeSnapshot] = OrderedDict()

    def get(self, device_id: str) -> Optional[KnowledgeSnapshot]:
        """Получает Snapshot из кэша (перемещает в конец для LRU)."""
        if device_id in self._snapshots:
            # Перемещаем в конец (последний использованный)
            self._snapshots.move_to_end(device_id)
            return self._snapshots[device_id]
        return None

    def put(self, device_id: str, snapshot: KnowledgeSnapshot):
        """Сохраняет Snapshot в кэш (с LRU eviction)."""
        if device_id in self._snapshots:
            # Обновляем существующий
            self._snapshots.move_to_end(device_id)
        
        self._snapshots[device_id] = snapshot
        
        # v1.6.9.8: LRU eviction если превышен лимит
        while len(self._snapshots) > self._max_size:
            # Удаляем самый старый (первый)
            self._snapshots.popitem(last=False)

    def invalidate(self, device_id: str):
        """Инвалидирует кэш для устройства."""
        if device_id in self._snapshots:
            del self._snapshots[device_id]

    def clear(self):
        """Очищает весь кэш."""
        self._snapshots.clear()
    
    def size(self) -> int:
        """Возвращает текущий размер кэша."""
        return len(self._snapshots)
    
    def max_size(self) -> int:
        """Возвращает максимальный размер кэша."""
        return self._max_size
