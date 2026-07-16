#!/usr/bin/env python3
"""Публичный API Usage Engine."""
from typing import Optional
from .engine import UsageEngine
from .explain import build_explanation
from .models import UsageProfile, UsageExplanation, DebugInfo
from .registry import ProviderRegistry

class UsageService:
    def __init__(self, history_service):
        self.engine = UsageEngine(history_service)
        for name, descriptor in ProviderRegistry.get_all().items():
            if name == "traffic_provider":
                self.engine.provider_manager.register(name, descriptor.provider_class(history_service))

    def get_profile(self, device_id: str) -> Optional[UsageProfile]:
        profile, _ = self.engine.analyze(device_id)
        return profile

    def explain(self, device_id: str) -> Optional[UsageExplanation]:
        profile, debug = self.engine.analyze(device_id)
        return build_explanation(profile, debug)

    def debug(self, device_id: str) -> Optional[DebugInfo]:
        _, debug = self.engine.analyze(device_id)
        return debug
