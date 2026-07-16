#!/usr/bin/env python3
"""Публичный API Presence Engine."""
from typing import Optional
from .engine import PresenceEngine
from .explain import build_explanation
from .models import PresenceProfile, PresenceExplanation, DebugInfo

class PresenceService:
    def __init__(self, history_service):
        self.engine = PresenceEngine(history_service)

    def get_profile(self, device_id: str) -> Optional[PresenceProfile]:
        profile, _ = self.engine.analyze(device_id)
        return profile

    def explain(self, device_id: str) -> Optional[PresenceExplanation]:
        profile, debug = self.engine.analyze(device_id)
        return build_explanation(profile, debug)  # Без metrics={} (Замечание №14)

    def debug(self, device_id: str) -> Optional[DebugInfo]:
        _, debug = self.engine.analyze(device_id)
        return debug
