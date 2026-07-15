#!/usr/bin/env python3
"""
Нормализация Raw Score в Confidence %.
Алгоритм изолирован и может быть заменён без изменения Evaluator.
"""


def normalize_score(raw_score: int, max_possible_score: int = 100) -> float:
    """
    Превращает Raw Score в Confidence %.
    
    Args:
        raw_score: Суммарный вес от всех источников
        max_possible_score: Максимально возможный вес (по умолчанию 100)
    
    Returns:
        Confidence в процентах (0.0 - 100.0)
    """
    if max_possible_score <= 0:
        return 0.0
    
    confidence = (raw_score / max_possible_score) * 100.0
    return min(confidence, 100.0)  # Не больше 100%
