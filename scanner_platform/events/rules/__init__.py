#!/usr/bin/env python3
"""Event Rules с автоматической регистрацией."""
from .base_rule import BaseEventRule
from .hostname_rule import HostnameRule
from .vendor_rule import VendorRule
from .capability_rule import CapabilityRule
from .summary_rule import SummaryRule
from .presence_rule import PresenceRule
from .session_rule import SessionRule
from ..registry import EventRuleRegistry

# Автоматическая регистрация всех правил при импорте
EventRuleRegistry.register(HostnameRule())
EventRuleRegistry.register(VendorRule())
EventRuleRegistry.register(CapabilityRule())
EventRuleRegistry.register(SummaryRule())
EventRuleRegistry.register(PresenceRule())
EventRuleRegistry.register(SessionRule())

__all__ = [
    "BaseEventRule",
    "HostnameRule",
    "VendorRule",
    "CapabilityRule",
    "SummaryRule",
    "PresenceRule",
    "SessionRule",
]
