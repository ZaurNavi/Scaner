#!/usr/bin/env python3
"""Hostname Change Rule."""
from typing import Tuple
from .base_rule import BaseEventRule
from ..base import DomainEvent, EventOrigin
from ..event_types import EventType
from ...diff.models import Change

class HostnameRule(BaseEventRule):
    """Правило для изменений hostname."""
    
    def supports(self, change: Change) -> bool:
        return (
            change.subject == "fact" and
            change.type.value == "UPDATED" and
            "hostname" in change.metadata.get("changed_fields", ())
        )
    
    def emit(self, change: Change, diff_id: str) -> Tuple[DomainEvent, ...]:
        old_hostname = change.old.get("hostname", "") if change.old else ""
        new_hostname = change.new.get("hostname", "") if change.new else ""
        
        event = DomainEvent.create(
            event_type=EventType.HOSTNAME_CHANGED.value,
            device_uuid=change.engine,  # Используем engine как device_uuid
            payload={
                "old_hostname": old_hostname,
                "new_hostname": new_hostname
            },
            source_diff_id=diff_id,
            source_change_id=change.change_id,
            origin=EventOrigin.RULE
        )
        
        return (event,)
