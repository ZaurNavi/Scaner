#!/usr/bin/env python3
"""
Identity Service — публичный API для Identity Engine.
"""

from __future__ import annotations

from typing import Optional, List

from .engine import IdentityEngine
from .repository import IdentityRepository
from .models import IdentityProfile
from history import HistoryService


class IdentityService:
    """Публичный API для работы с Identity."""
    
    def __init__(self, history_service: HistoryService, repository: IdentityRepository):
        self.engine = IdentityEngine(history_service, repository)
        self.repo = repository
        self.history = history_service

    def get_identity(self, device_id: str) -> Optional[IdentityProfile]:
        """Получает IdentityProfile для устройства."""
        return self.repo.load_identity(device_id)

    def get_profile(self, device_id: str) -> Optional[IdentityProfile]:
        """Алиас для get_identity."""
        return self.get_identity(device_id)

    def get_statistics(self, device_id: str) -> Optional[dict]:
        """Получает статистику Identity."""
        profile = self.get_identity(device_id)
        if profile:
            return {
                "statistics": profile.statistics,
                "traffic_statistics": profile.traffic_statistics
            }
        return None

    def get_network(self, device_id: str) -> Optional[dict]:
        """Получает сетевой профиль."""
        profile = self.get_identity(device_id)
        if profile:
            return profile.network
        return None

    def refresh(self, device_id: str) -> IdentityProfile:
        """Пересчитывает Identity для устройства."""
        return self.engine.build_identity(device_id)

    def refresh_all(self, device_ids: List[str]) -> List[IdentityProfile]:
        """Пересчитывает Identity для всех устройств."""
        return self.engine.refresh_all(device_ids)

    def exists(self, device_id: str) -> bool:
        """Проверяет существование Identity."""
        return self.repo.exists(device_id)

    def list_identities(self) -> List[IdentityProfile]:
        """Список всех Identity (заглушка для будущего)."""
        # TODO: Реализовать запрос всех Identity из БД
        return []
