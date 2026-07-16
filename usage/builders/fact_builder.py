#!/usr/bin/env python3
"""Fact Builder: создает UsageFact из результатов Evaluator."""
from datetime import datetime
from typing import List, Dict, Any
from ..models import UsageFact, UsageQuality, UsageMetricSet, UsageFeatureSet
from ..categories import UsageCategory, UsageStatus

class FactBuilder:
    """Создает UsageFact с полным Explain Trace."""
    
    def build_fact(
        self,
        category: UsageCategory,
        rule_id: str,
        rule_name: str,
        matched_features: List[str],
        feature_values: Dict[str, Any],
        metrics: UsageMetricSet,
        features: UsageFeatureSet,
        weight: int,
        quality: UsageQuality = None
    ) -> UsageFact:
        """Создает UsageFact с полным Explain Trace."""
        
        primary_feature = matched_features[0] if matched_features else "unknown"
        measured_value = feature_values.get(primary_feature, None)
        
        # Вычисляем confidence (исправлено: без деления на 100)
        confidence = self._calculate_confidence(weight, matched_features, features)
        
        # Определяем status
        status = UsageStatus.HIGH if confidence >= 60 else UsageStatus.MEDIUM if confidence >= 40 else UsageStatus.LOW
        
        # Строим Explain Trace
        explain_trace = {
            "rule": {"id": rule_id, "name": rule_name, "weight": weight},
            "features": {f: feature_values.get(f) for f in matched_features},
            "metrics": {f: metrics.get(f).value if metrics.get(f) else None for f in matched_features},
            "confidence_calculation": f"weight={weight}, features={len(matched_features)}"
        }
        
        reasons = [f"{rule_name}: {', '.join([f'{f}={feature_values.get(f)}' for f in matched_features])}"]
        
        # Собираем sources
        sources = []
        for f in matched_features:
            feature = features.get(f)
            if feature and feature.sources:
                sources.extend(feature.sources)
        sources = list(set(sources))
        
        return UsageFact(
            category=category,
            feature=primary_feature,
            value=category.value,
            measured_value=measured_value,
            score=weight,
            confidence=confidence,
            quality=quality,
            status=status,
            matched_rules=[rule_id],
            sources=sources,
            reasons=reasons,
            explain_trace=explain_trace,
            generated_at=datetime.now(),
            version="1.0.0"
        )
    
    def _calculate_confidence(self, weight: int, matched_features: List[str], features: UsageFeatureSet) -> float:
        """Вычисляет confidence (исправлено: без деления на 100)."""
        base_confidence = weight
        
        # Увеличиваем confidence, если больше features совпало
        feature_bonus = len(matched_features) * 5
        
        # Учитываем качество features (confidence уже в 0..100)
        feature_confidences = [features.get(f).confidence for f in matched_features if features.get(f)]
        avg_feature_confidence = sum(feature_confidences) / max(len(feature_confidences), 1)
        quality_multiplier = avg_feature_confidence / 100.0  # Нормализация к 0..1
        
        final_confidence = min((base_confidence + feature_bonus) * quality_multiplier, 100.0)
        
        return final_confidence
