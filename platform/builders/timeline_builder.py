#!/usr/bin/env python3
"""Timeline Builder."""
from typing import List
from .base import Builder
from platform.timeline.models import Timeline, TimelineEvent
from platform.timeline.provider import TimelineProvider

class TimelineBuilder(Builder):
    """Строит Timeline из Providers."""
    
    def __init__(self):
        self._providers: List[TimelineProvider] = []
    
    @property
    def name(self) -> str:
        return "timeline_builder"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def register_provider(self, provider: TimelineProvider):
        """Регистрирует Timeline Provider."""
        self._providers.append(provider)
    
    def build(self, device_id: str) -> Timeline:
        """Строит Timeline для устройства."""
        all_events: List[TimelineEvent] = []
        
        for provider in self._providers:
            try:
                result = provider.extract(device_id)
                all_events.extend(result.events)
            except Exception as e:
                print(f"  [TIMELINE] ⚠️ Provider {provider.name} failed: {e}")
        
        all_events.sort(key=lambda e: e.timestamp)
        
        return Timeline(
            events=all_events,
            device_id=device_id
        )
