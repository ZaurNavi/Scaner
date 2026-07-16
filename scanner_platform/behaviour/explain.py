#!/usr/bin/env python3
"""Explain Builder для Behaviour Engine."""
from typing import List, Dict, Any
from ..facts.models import Fact

class BehaviourExplainBuilder:
    """Строит Explain Trace для всех фактов движка."""
    
    @staticmethod
    def build_explain(facts: List[Fact], metrics: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Строит полный Explain Trace.
        
        Структура:
        Fact → Rule → Features → Metrics
        """
        explain = {
            "engine": "behaviour",
            "facts": [],
            "confidence_trace": {
                "metric": 0.9,
                "feature": 0.85,
                "rule": 0.8,
                "fact": 0.0
            }
        }
        
        for fact in facts:
            fact_explain = {
                "fact_id": fact.id,
                "category": fact.category,
                "confidence": fact.confidence,
                "chain": {
                    "rule": fact.matched_rules,
                    "features": fact.matched_features,
                    "metrics": BehaviourExplainBuilder._get_metrics_for_features(
                        fact.matched_features, features, metrics
                    )
                }
            }
            explain["facts"].append(fact_explain)
            
            # Обновляем среднюю confidence
            if explain["facts"]:
                avg_confidence = sum(f["confidence"] for f in explain["facts"]) / len(explain["facts"])
                explain["confidence_trace"]["fact"] = avg_confidence / 100.0
        
        return explain
    
    @staticmethod
    def _get_metrics_for_features(features: List[str], feature_values: Dict[str, Any], metrics: Dict[str, Any]) -> List[str]:
        """Определяет, какие метрики привели к данным фичам."""
        # Упрощённо: возвращаем названия фич как источники
        return features
