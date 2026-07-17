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
    Детерминированный и идемпотентный.
    """
    
    def generate(self, diff: ProfileDiff) -> DomainEventSet:
        """
        Генерирует DomainEventSet из ProfileDiff.
        Детерминированный и идемпотентный.
        """
        # Идемпотентность: EMPTY_DIFF → EMPTY_EVENT_SET
        if diff is EMPTY_DIFF:
            return EMPTY_EVENT_SET
        
        events: List[DomainEvent] = []
        
        # Извлекаем device_uuid и occurred_at из Diff для детерминированности
        device_uuid = diff.identity_uuid
        occurred_at = diff.created_at
        
        # Получаем правила из Registry
        rules = EventRuleRegistry.get_all()
        
        # O(n): один проход по всем изменениям
        for change in diff.changes:
            # Проходим по всем правилам
            for rule in rules:
                if rule.supports(change):
                    # Правило может вернуть 0..N событий
                    rule_events = rule.emit(change, diff.diff_id, device_uuid, occurred_at)
                    events.extend(rule_events)
        
        # Сортируем для детерминированности (стабильная сортировка)
        events.sort(key=lambda e: (e.event_type, e.event_id, e.source_change_id))
        
        return DomainEventSet(
            events=tuple(events),
            generated_at=occurred_at  # Используем время из Diff
        )
