#!/usr/bin/env python3
"""
Identity Engine — координатор формирования IdentityProfile.
"""

from __future__ import annotations

from typing import List

from .builder import IdentityBuilder
from .repository import IdentityRepository
from .models import IdentityProfile, DeviceContext
from history import HistoryService


class IdentityEngine:
    """Координатор Identity Engine."""
    
    def __init__(self, history_service: HistoryService, repository: IdentityRepository):
        self.history = history_service
        self.repo = repository
        self.builder = IdentityBuilder()

    def build_identity(self, device_id: str) -> IdentityProfile:
        """Строит IdentityProfile для устройства."""
        # Загружаем контекст через History Service
        device_history = self.history.get_device_history(device_id)
        
        context = DeviceContext(
            device_id=device_id,
            mac=device_history.mac,
            first_seen=device_history.first_seen,
            last_seen=device_history.last_seen,
            snapshots=device_history.snapshots,
            observations=device_history.observations,
            events=device_history.events
        )
        
        # Строим профиль
        profile = self.builder.build(context)
        
        # Сохраняем через Repository
        if self.repo.exists(device_id):
            self.repo.update_identity(profile)
        else:
            self.repo.save_identity(profile)
        
        return profile

    def refresh_all(self, device_ids: List[str]) -> List[IdentityProfile]:
        """Обновляет Identity для всех устройств."""
        profiles = []
        for device_id in device_ids:
            profile = self.build_identity(device_id)
            profiles.append(profile)
        return profiles
