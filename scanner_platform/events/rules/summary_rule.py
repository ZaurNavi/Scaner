#!/usr/bin/env python3
"""Summary Change Rule."""
from typing import Tuple
from datetime import datetime
from .base_rule import BaseEventRule
from ..base import DomainEvent, EventOrigin
from ..event_types import EventType
from ...diff.models import Change

class SummaryRule(BaseEventRule):
    """Правило для изменений summary."""
    
    def supports(self, change: Change) -> bool:
        return change.subject == "summary"
    
    def emit(self, change: Change, diff_id: str, device_uuid: str, occurred_at: datetime) -> Tuple[DomainEvent, ...]:
        event = DomainEvent.create(
            event_type=EventType.SUMMARY_CHANGED.value,
            device_uuid=device_uuid,
            payload={
                "field": change.category,
                "old_value": change.old,
                "new_value": change.new,
                "delta": change.delta
            },
            source_diff_id=diff_id,
            source_change_id=change.change_id,
            occurred_at=occurred_at,
            origin=EventOrigin.RULE
        )
        
        return (event,)
