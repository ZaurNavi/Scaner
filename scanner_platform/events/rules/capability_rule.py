#!/usr/bin/env python3
"""Capability Change Rule."""
from typing import Tuple
from datetime import datetime
from .base_rule import BaseEventRule
from ..base import DomainEvent, EventOrigin
from ..event_types import EventType
from ...diff.models import Change, ChangeType

class CapabilityRule(BaseEventRule):
    """Правило для изменений capabilities."""
    
    def supports(self, change: Change) -> bool:
        return change.subject == "capability"
    
    def emit(self, change: Change, diff_id: str, device_uuid: str, occurred_at: datetime) -> Tuple[DomainEvent, ...]:
        events = []
        
        if change.type == ChangeType.ADDED:
            event = DomainEvent.create(
                event_type=EventType.CAPABILITY_ADDED.value,
                device_uuid=device_uuid,
                payload={
                    "capability": change.new
                },
                source_diff_id=diff_id,
                source_change_id=change.change_id,
                occurred_at=occurred_at,
                origin=EventOrigin.RULE
            )
            events.append(event)
        
        elif change.type == ChangeType.REMOVED:
            event = DomainEvent.create(
                event_type=EventType.CAPABILITY_REMOVED.value,
                device_uuid=device_uuid,
                payload={
                    "capability": change.old
                },
                source_diff_id=diff_id,
                source_change_id=change.change_id,
                occurred_at=occurred_at,
                origin=EventOrigin.RULE
            )
            events.append(event)
        
        return tuple(events)
