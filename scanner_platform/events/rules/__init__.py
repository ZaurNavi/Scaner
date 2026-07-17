#!/usr/bin/env python3
"""Event Rules."""
from .base_rule import BaseEventRule
from .hostname_rule import HostnameRule
from .vendor_rule import VendorRule
from .capability_rule import CapabilityRule
from .summary_rule import SummaryRule
from .presence_rule import PresenceRule
from .session_rule import SessionRule

# ИСПРАВЛЕНО: убрана автоматическая регистрация для предотвращения circular import
# Регистрация происходит в events/__init__.py после импорта EventRuleRegistry

__all__ = [
    "BaseEventRule",
    "HostnameRule",
    "VendorRule",
    "CapabilityRule",
    "SummaryRule",
    "PresenceRule",
    "SessionRule",
]
