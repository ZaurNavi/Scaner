#!/usr/bin/env python3
"""Session Change Rule."""
from typing import Tuple
from datetime import datetime
from .base_rule import BaseEventRule
from ..base import DomainEvent, EventOrigin
from ..event_types import EventType
from ..constants import SubjectType, CategoryType
from ...diff.models import Change

class SessionRule(BaseEventRule):
    """Правило для изменений sessions."""
    
    def supports(self, change: Change) -> bool:
        return (
            change.subject == SubjectType.SUMMARY and
            change.category == CategoryType.SESSIONS and
            change.delta is not None
        )
    
    def emit(self, change: Change, diff_id: str, device_uuid: str, occurred_at: datetime) -> Tuple[DomainEvent, ...]:
        events = []
        
        if change.delta > 0:
            # Сессии увеличились
            event = DomainEvent.create(
                event_type=EventType.SESSION_STARTED.value,
                device_uuid=device_uuid,
                payload={
                    "old_sessions": change.old,
                    "new_sessions": change.new,
                    "delta": change.delta
                },
                source_diff_id=diff_id,
                source_change_id=change.change_id,
                occurred_at=occurred_at,
                origin=EventOrigin.RULE
            )
            events.append(event)
        
        elif change.delta < 0:
            # Сессии уменьшились
            event = DomainEvent.create(
                event_type=EventType.SESSION_ENDED.value,
                device_uuid=device_uuid,
                payload={
                    "old_sessions": change.old,
                    "new_sessions": change.new,
                    "delta": change.delta
                },
                source_diff_id=diff_id,
                source_change_id=change.change_id,
                occurred_at=occurred_at,
                origin=EventOrigin.RULE
            )
            events.append(event)
        
        return tuple(events)
