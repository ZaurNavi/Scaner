#!/usr/bin/env python3
"""Statistics Builder — строит статистику знаний."""
from typing import List, Any, Dict

class StatisticsBuilder:
    """Строит Statistics для Knowledge Snapshot."""
    
    @staticmethod
    def build(facts: List[Any]) -> Dict[str, Any]:
        """
        Строит Statistics из Platform Facts.
        
        ИСПРАВЛЕНО: убран coverage_average (это не то же самое что confidence).
        """
        if not facts:
            return {
                "facts_total": 0,
                "facts_by_category": {},
                "average_confidence": 0.0,
                "highest_confidence": 0.0
            }
        
        # Подсчет по категориям
        facts_by_category = {}
        for fact in facts:
            category = fact.category
            facts_by_category[category] = facts_by_category.get(category, 0) + 1
        
        # Уверенность
        confidences = [fact.confidence for fact in facts]
        avg_confidence = sum(confidences) / len(confidences)
        highest_confidence = max(confidences)
        
        return {
            "facts_total": len(facts),
            "facts_by_category": facts_by_category,
            "average_confidence": avg_confidence,
            "highest_confidence": highest_confidence
        }
