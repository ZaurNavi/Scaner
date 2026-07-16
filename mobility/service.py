#!/usr/bin/env python3
"""Публичный API Mobility Engine."""
from typing import Optional
from .engine import MobilityEngine
from .explain import build_explanation
from .models import MobilityProfile, MobilityExplanation, DebugInfo

class MobilityService:
    def __init__(self, behaviour_service, session_engine, history_service):
        self.engine = MobilityEngine(behaviour_service, session_engine, history_service)
        self._last_metrics = {} # Храним для Explain

    def get_profile(self, device_id: str) -> Optional[MobilityProfile]:
        profile, _ = self.engine.analyze(device_id)
        return profile

    def explain(self, device_id: str) -> Optional[MobilityExplanation]:
        profile, debug = self.engine.analyze(device_id)
        # В реальной реализации metrics нужно возвращать из engine или кэшировать
        # Для простоты здесь передаем пустой dict, но архитектура готова
        return build_explanation(profile, debug, {})

    def debug(self, device_id: str) -> Optional[DebugInfo]:
        _, debug = self.engine.analyze(device_id)
        return debug
