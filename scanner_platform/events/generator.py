#!/usr/bin/env python3
"""Event Generator - генератор доменных событий."""
from typing import List
from datetime import datetime
from ..diff.models import ProfileDiff, EMPTY_DIFF
from .base import DomainEvent
from .event_set import DomainEventSet, EMPTY_EVENT_SET
from .registry import EventRuleRegistry

class EventGenerator:
    """
    Генератор доменных событий.
    Не содержит бизнес-логики, только Registry.
    O(n) сложность, где n = количество Change.
    """
    
    def __init__(self):
        self._rules = EventRuleRegistry.get_all()
    
    def generate(self, diff: ProfileDiff) -> DomainEventSet:
        """
        Генерирует DomainEventSet из ProfileDiff.
        Детерминированный и идемпотентный.
        """
        # Идемпотентность: EMPTY_DIFF → EMPTY_EVENT_SET
        if diff is EMPTY_DIFF:
            return EMPTY_EVENT_SET
        
        events: List[DomainEvent] = []
        
        # O(n): один проход по всем изменениям
        for change in diff.changes:
            # Проходим по всем правилам
            for rule in self._rules:
                if rule.supports(change):
                    # Правило может вернуть 0..N событий
                    rule_events = rule.emit(change, diff.diff_id)
                    events.extend(rule_events)
        
        # Сортируем для детерминированности
        events.sort(key=lambda e: (e.event_type, e.event_id))
        
        return DomainEventSet(
            events=tuple(events),
            generated_at=datetime.now()
        )
