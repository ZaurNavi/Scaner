#!/usr/bin/env python3
"""Facts Builder."""
from datetime import datetime
from typing import Dict, Any, List
from uuid import uuid4
from .base import Builder
from platform.facts.models import Fact, FactStatus
from platform.registry.rule_registry import RuleRegistry
from platform.rules.evaluator import RuleEvaluator

class FactsBuilder(Builder):
    """Строит Facts из Features."""
    
    def __init__(self, engine_name: str):
        self.engine_name = engine_name
        self.evaluator = RuleEvaluator()
    
    @property
    def name(self) -> str:
        return "facts_builder"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def build(self, features_data: Dict[str, Any]) -> List[Fact]:
        """Строит Facts из Features."""
        features = features_data.get("features", {})
        
        # Получаем правила для этого движка
        rules = RuleRegistry.get_by_engine(self.engine_name)
        
        facts = []
        for rule_id, rule in rules.items():
            try:
                # Evaluator возвращает только True/False
                matched = self.evaluator.evaluate(rule, features)
                
                if matched:
                    # Builder строит Fact
                    fact = self._build_fact(rule, features)
                    facts.append(fact)
            except Exception as e:
                print(f"  [FACTS] ⚠️ Failed to evaluate rule {rule_id}: {e}")
        
        return facts
    
    def _build_fact(self, rule, features: Dict[str, Any]) -> Fact:
        """Строит Fact из правила."""
        matched_features = [c.feature for c in rule.conditions]
        
        # Вычисляем confidence
        confidence = self._calculate_confidence(rule.weight, matched_features, features)
        
        # Определяем status
        status = FactStatus.HIGH if confidence >= 60 else FactStatus.MEDIUM if confidence >= 40 else FactStatus.LOW
        
        # Строим Explain
        explain = {
            "rule": {"id": rule.id, "name": rule.name, "weight": rule.weight},
            "features": {f: features.get(f) for f in matched_features},
            "confidence_calculation": f"weight={rule.weight}, features={len(matched_features)}"
        }
        
        return Fact(
            id=str(uuid4()),
            engine=self.engine_name,
            category=rule.category,
            status=status,
            confidence=confidence,
            quality=0.9,
            sources=[self.engine_name],
            matched_rules=[rule.id],
            matched_features=matched_features,
            explain=explain,
            generated_at=datetime.now()
        )
    
    def _calculate_confidence(self, weight: int, matched_features: List[str], features: Dict[str, Any]) -> float:
        """Вычисляет confidence."""
        base_confidence = weight
        feature_bonus = len(matched_features) * 5
        final_confidence = min(base_confidence + feature_bonus, 100.0)
        return final_confidence
