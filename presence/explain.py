#!/usr/bin/env python3
"""Explain API: возвращает реальные метрики и execution_order (Замечение №10, №14)."""
from .models import PresenceExplanation, DebugInfo, PresenceProfile

def build_explanation(profile: PresenceProfile, debug: DebugInfo) -> PresenceExplanation:
    sources = list(set([src for f in profile.features.values() for src in f.sources]))
    
    # Замечение №10: execution_order
    execution_order = [
        "History Provider",
        "Metrics Builder",
        "Timeline Factory",
        "Feature Builder",
        "Evaluator",
        "Profile Builder"
    ]
    
    return PresenceExplanation(
        timeline=profile.timeline,
        metrics=profile.metrics,  # Замечание №14: реальные метрики
        features=profile.features,
        matched_rules=debug.matched_rules,
        skipped_rules=debug.skipped_rules,
        facts=profile.facts,
        profile=profile,
        missing_features=debug.missing_features,
        providers=list(debug.provider_times.keys()),
        sources=sources,
        execution_order=execution_order
    )
