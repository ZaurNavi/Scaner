#!/usr/bin/env python3
"""Summary Builder — строит краткое описание устройства."""
from datetime import datetime
from typing import List, Any, Dict, Optional

class SummaryBuilder:
    """Строит Summary для Knowledge Snapshot."""
    
    @staticmethod
    def build(
        device_id: str,
        facts: List[Any],
        history_service=None  # ДОБАВЛЕНО: для получения реальной истории
    ) -> Dict[str, Any]:
        """
        Строит Summary из Platform Facts и History.
        
        ИСПРАВЛЕНО: history_depth берется из History, а не из Facts.
        """
        if not facts:
            return {
                "known_since": None,
                "history_depth": 0,
                "facts_count": 0,
                "categories": [],
                "average_confidence": 0.0,
                "first_seen": None,
                "last_seen": None
            }
        
        # === ИСПРАВЛЕНО: Получаем реальную историю из HistoryService ===
        if history_service:
            try:
                history = history_service.get_device_history(device_id)
                first_seen = getattr(history, 'first_seen', None)
                last_seen = getattr(history, 'last_seen', None)
            except Exception:
                first_seen = None
                last_seen = None
        else:
            # Fallback: используем timestamps из Facts
            timestamps = []
            for fact in facts:
                if hasattr(fact, 'generated_at') and fact.generated_at:
                    timestamps.append(fact.generated_at)
            first_seen = min(timestamps) if timestamps else None
            last_seen = max(timestamps) if timestamps else None
        
        # Вычисляем глубину истории
        if first_seen and last_seen:
            history_depth = (last_seen - first_seen).days
        else:
            history_depth = 0
        
        # Категории
        categories = list(set(fact.category for fact in facts))
        
        # Средняя уверенность
        avg_confidence = sum(fact.confidence for fact in facts) / len(facts)
        
        return {
            "known_since": first_seen,
            "history_depth": history_depth,
            "facts_count": len(facts),
            "categories": categories,
            "average_confidence": avg_confidence,
            "first_seen": first_seen,
            "last_seen": last_seen
        }
