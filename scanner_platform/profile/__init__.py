#!/usr/bin/env python3
"""Unified Device Profile — единое представление устройства."""

from .profile import UnifiedDeviceProfile
from .result import ProfileResult, ProfileExecution
from .service import ProfileService
from .builder import ProfileBuilder
from .cache import ProfileSnapshotCache
from .models import (
    ProfileSummary, ProfileStatistics, ProfileCoverage,
    ProfileConfidence, IdentityState, IdentityReference,
    ProfileCategories
)
from .query.api import ProfileQueryBuilder
from .explain.graph import ExplainGraph
from .explain.service import ExplainService
from .capability.resolver import CapabilityResolver
from .capability.registry import CapabilityRegistry, CapabilityDescriptor

__all__ = [
    "UnifiedDeviceProfile",
    "ProfileResult",
    "ProfileExecution",
    "ProfileService",
    "ProfileBuilder",
    "ProfileSnapshotCache",
    "ProfileSummary",
    "ProfileStatistics",
    "ProfileCoverage",
    "ProfileConfidence",
    "IdentityState",
    "IdentityReference",
    "ProfileCategories",
    "ProfileQueryBuilder",
    "ExplainGraph",
    "ExplainService",
    "CapabilityResolver",
    "CapabilityRegistry",
    "CapabilityDescriptor",
]
