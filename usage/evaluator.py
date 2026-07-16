#!/usr/bin/env python3
"""Evaluator: применяет правила к Features (возвращает dict для debug)."""
from typing import List, Dict, Any, Tuple
from .models import UsageFeatureSet, UsageMetricSet
from .rules import get_enabled_rules, evaluate_condition

class UsageEvaluator:
    """Применяет правила к Features и возвращает matched rules."""
    
    def evaluate(self, feature_set: UsageFeatureSet, metrics: UsageMetricSet) -> Tuple[List[Dict], Dict]:
        """Применяет правила и возвращает matched rules + debug dict."""
        matched_rules = []
        rules = get_enabled_rules()
        
        debug_info = {
            "evaluated": [],
            "matched": [],
            "skipped": [],
            "all_rules": rules
        }

        for rule in rules:
            rule_id = rule.id
            
            # Проверяем наличие всех required features
            missing_features = []
            for condition in rule.conditions:
                if condition.feature not in feature_set or not feature_set[condition.feature].availability:
                    missing_features.append(condition.feature)
            
            if missing_features:
                debug_info["skipped"].append(f"{rule_id} (Missing features: {missing_features})")
                continue

            debug_info["evaluated"].append(rule_id)
            
            # Проверяем ВСЕ условия правила
            condition_results = []
            matched_features = []
            feature_values = {}
            
            for condition in rule.conditions:
                feature = feature_set[condition.feature]
                result = evaluate_condition(condition.operator, feature.value, condition.threshold)
                condition_results.append(result)
                if result:
                    matched_features.append(condition.feature)
                    feature_values[condition.feature] = feature.value
            
            # Применяем логику (AND, OR, NOT, ANY, ALL)
            all_conditions_met = self._apply_logic(rule.logic.value, condition_results)
            
            if all_conditions_met:
                debug_info["matched"].append(rule_id)
                matched_rules.append({
                    "rule": rule,
                    "matched_features": matched_features,
                    "feature_values": feature_values
                })
                
        return matched_rules, debug_info
    
    def _apply_logic(self, logic: str, results: List[bool]) -> bool:
        """Применяет логику (AND, OR, NOT, ANY, ALL)."""
        if not results:
            return False
        
        if logic == "AND":
            return all(results)
        elif logic == "OR":
            return any(results)
        elif logic == "NOT":
            return not any(results)
        elif logic == "ANY":
            return any(results)
        elif logic == "ALL":
            return all(results)
        
        return False
