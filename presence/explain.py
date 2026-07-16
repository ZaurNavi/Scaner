#!/usr/bin/env python3
"""Explain API: возвращает реальные метрики из конвейера (Замечание №14)."""
from .models import PresenceExplanation, DebugInfo, PresenceProfile

def build_explanation(profile: PresenceProfile, debug: DebugInfo) -> PresenceExplanation:
    sources = list(set([src for f in profile.features.values() for src in f.sources]))
    
    return PresenceExplanation(
        timeline=profile.timeline,
        metrics=profile.metrics,  # Реальные метрики, не пустой dict
        features=profile.features,
        matched_rules=debug.matched_rules,
        skipped_rules=debug.skipped_rules,
        facts=profile.facts,
        profile=profile,
        missing_features=debug.missing_features,
        providers=list(debug.provider_times.keys()),
        sources=sources
    )
