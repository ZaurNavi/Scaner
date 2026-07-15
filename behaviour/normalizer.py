#!/usr/bin/env python3
"""
Нормализация Raw Score в Confidence %.
"""

from .constants import MAX_RAW_SCORE


def normalize_score(raw_score: int, max_possible_score: int = MAX_RAW_SCORE) -> float:
    """
    Превращает Raw Score в Confidence %.
    
    Args:
        raw_score: Суммарный вес от всех правил
        max_possible_score: Максимально возможный вес
    
    Returns:
        Confidence в процентах (0.0 - 100.0)
    """
    if max_possible_score <= 0:
        return 0.0
    
    confidence = (raw_score / max_possible_score) * 100.0
    return min(confidence, 100.0)
