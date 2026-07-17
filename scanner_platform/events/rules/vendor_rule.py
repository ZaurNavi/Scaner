#!/usr/bin/env python3
"""Vendor Change Rule."""
from typing import Tuple
from datetime import datetime
from .base_rule import BaseEventRule
from ..base import DomainEvent, EventOrigin
from ..event_types import EventType
from ...diff.models import Change

class VendorRule(BaseEventRule):
    """Правило для изменений vendor."""
    
    def supports(self, change: Change) -> bool:
        return (
            change.subject == "fact" and
            change.type.value == "UPDATED" and
            "vendor" in change.metadata.get("changed_fields", ())
        )
    
    def emit(self, change: Change, diff_id: str, device_uuid: str, occurred_at: datetime) -> Tuple[DomainEvent, ...]:
        old_vendor = change.old.get("vendor", "") if change.old else ""
        new_vendor = change.new.get("vendor", "") if change.new else ""
        
        events = []
        
        # VendorChanged
        vendor_event = DomainEvent.create(
            event_type=EventType.VENDOR_CHANGED.value,
            device_uuid=device_uuid,
            payload={
                "old_vendor": old_vendor,
                "new_vendor": new_vendor
            },
            source_diff_id=diff_id,
            source_change_id=change.change_id,
            occurred_at=occurred_at,
            origin=EventOrigin.RULE
        )
        events.append(vendor_event)
        
        # DeviceIdentityChanged (дополнительное событие)
        identity_event = DomainEvent.create(
            event_type=EventType.DEVICE_IDENTITY_CHANGED.value,
            device_uuid=device_uuid,
            payload={
                "field": "vendor",
                "old_value": old_vendor,
                "new_value": new_vendor
            },
            source_diff_id=diff_id,
            source_change_id=change.change_id,
            occurred_at=occurred_at,
            origin=EventOrigin.RULE
        )
        events.append(identity_event)
        
        return tuple(events)
