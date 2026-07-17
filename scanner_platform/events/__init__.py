#!/usr/bin/env python3
"""Domain Event Layer v1.6.8"""

from .base import DomainEvent, EventOrigin
from .event_types import EventType
from .event_set import DomainEventSet, EMPTY_EVENT_SET
from .event_query import EventQuery
from .registry import EventRuleRegistry
from .generator import EventGenerator
from .serializer import EventSerializer
from .constants import SubjectType, CategoryType
from .exceptions import InvalidDiffError, EventGenerationError

# Импорт правил автоматически регистрирует их в Registry
from .rules import (
    BaseEventRule,
    HostnameRule,
    VendorRule,
    CapabilityRule,
    SummaryRule,
    PresenceRule,
    SessionRule
)

__all__ = [
    "DomainEvent",
    "EventOrigin",
    "EventType",
    "DomainEventSet",
    "EMPTY_EVENT_SET",
    "EventQuery",
    "EventRuleRegistry",
    "EventGenerator",
    "EventSerializer",
    "SubjectType",
    "CategoryType",
    "InvalidDiffError",
    "EventGenerationError",
    "BaseEventRule",
    "HostnameRule",
    "VendorRule",
    "CapabilityRule",
    "SummaryRule",
    "PresenceRule",
    "SessionRule",
]
