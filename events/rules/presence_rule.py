#!/usr/bin/env python3
"""Presence Change Rule."""
from typing import Tuple
from datetime import datetime
from .base_rule import BaseEventRule
from ..base import DomainEvent, EventOrigin
from ..event_types import EventType
from ..constants import SubjectType, CategoryType
from ...diff.models import Change, ChangeType

class PresenceRule(BaseEventRule):
    """Правило для изменений presence."""
    
    def supports(self, change: Change) -> bool:
        # ИСПРАВЛЕНО: единый стиль с ==
        if change.subject != SubjectType.FACT:
            return False
        if change.category != CategoryType.PRESENCE:
            return False
        if change.type == ChangeType.ADDED:
            return True
        if change.type == ChangeType.REMOVED:
            return True
        return False
    
    def emit(self, change: Change, diff_id: str, device_uuid: str, occurred_at: datetime) -> Tuple[DomainEvent, ...]:
        events = []
        
        if change.type == ChangeType.ADDED:
            event = DomainEvent.create(
                event_type=EventType.PRESENCE_APPEARED.value,
                device_uuid=device_uuid,
                payload={
                    "fact_id": change.metadata.get("fact_id"),
                    "engine": change.engine
                },
                source_diff_id=diff_id,
                source_change_id=change.change_id,
                occurred_at=occurred_at,
                origin=EventOrigin.RULE
            )
            events.append(event)
        
        elif change.type == ChangeType.REMOVED:
            event = DomainEvent.create(
                event_type=EventType.PRESENCE_DISAPPEARED.value,
                device_uuid=device_uuid,
                payload={
                    "fact_id": change.metadata.get("fact_id"),
                    "engine": change.engine
                },
                source_diff_id=diff_id,
                source_change_id=change.change_id,
                occurred_at=occurred_at,
                origin=EventOrigin.RULE
            )
            events.append(event)
        
        return tuple(events)
