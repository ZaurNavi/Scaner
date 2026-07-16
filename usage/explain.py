#!/usr/bin/env python3
"""Explain API: возвращает полный трассировочный путь."""
from .models import UsageExplanation, DebugInfo, UsageProfile

def build_explanation(profile: UsageProfile, debug: DebugInfo) -> UsageExplanation:
    sources = list(set([src for f in profile.features.values() for src in f.sources]))
    
    execution_order = [
        "Traffic Provider",
        "Metrics Builder",
        "Timeline Builder",
        "Feature Builder",
        "Evaluator",
        "Profile Builder"
    ]
    
    confidence_trace = {
        "provider": 0.9,
        "metric": profile.metric_coverage / 100.0,
        "feature": profile.feature_coverage / 100.0,
        "rule": profile.rule_match_ratio / 100.0,
        "fact": sum(f.confidence for f in profile.facts) / max(len(profile.facts), 1) / 100.0
    }
    
    return UsageExplanation(
        timeline=profile.timeline,
        metrics=profile.metrics,
        provider_quality=profile.metrics.provider_quality,
        features=profile.features,
        matched_rules=debug.matched_rules,
        skipped_rules=debug.skipped_rules,
        facts=profile.facts,
        profile=profile,
        missing_features=debug.missing_features,
        providers=list(debug.provider_times.keys()),
        sources=sources,
        execution_order=execution_order,
        confidence_trace=confidence_trace
    )
