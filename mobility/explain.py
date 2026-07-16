#!/usr/bin/env python3
"""Модуль для генерации Explain информации из реального Pipeline."""
from .models import MobilityExplanation, DebugInfo, MobilityProfile, MobilityFeatureSet

def build_explanation(profile: MobilityProfile, debug: DebugInfo, metrics: dict) -> MobilityExplanation:
    sources = list(set([src for f in profile.features.values() for src in f.sources]))
    
    return MobilityExplanation(
        metrics=metrics, # <-- ИСПРАВЛЕНО: реальные метрики конвейера
        features=profile.features,
        matched_rules=debug.matched_rules,
        skipped_rules=debug.skipped_rules,
        facts=profile.facts,
        profile=profile,
        missing_features=debug.missing_features,
        providers=list(debug.provider_times.keys()),
        sources=sources
    )
