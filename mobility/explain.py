#!/usr/bin/env python3
"""Модуль для генерации Explain и Debug информации."""
from .models import MobilityExplanation, DebugInfo, MobilityProfile, MobilityFeatureSet
from .rules import get_enabled_rules

def build_explanation(profile: MobilityProfile, debug: DebugInfo, metrics: dict) -> MobilityExplanation:
    matched = []
    skipped = []
    rules = get_enabled_rules()
    
    for rule in rules:
        if any(rule.id in f.matched_rules for f in profile.facts):
            matched.append(rule.id)
        else:
            skipped.append(rule.id)
            
    sources = list(set([src for f in profile.features.values() for src in f.sources]))
    
    return MobilityExplanation(
        metrics=metrics,
        features=profile.features,
        matched_rules=matched,
        skipped_rules=skipped,
        facts=profile.facts,
        profile=profile,
        missing_features=debug.missing_features,
        providers=debug.used_providers,
        sources=sources
    )
