#!/usr/bin/env python3
"""ProfileBuilder — строит UnifiedDeviceProfile через KnowledgeFacade."""
from datetime import datetime
from typing import Dict, Any
from .profile import UnifiedDeviceProfile
from .models import (
    ProfileSummary, ProfileStatistics, ProfileCoverage,
    ProfileConfidence, IdentityState, IdentityReference, ProfileCategories
)
from .facets.summary import SummaryFacet
from .facets.statistics import StatisticsFacet
from .facets.presence import PresenceFacet
from .facets.usage import UsageFacet
from .facets.behaviour import BehaviourFacet
from .facets.mobility import MobilityFacet
from .facets.capability import CapabilityFacet
from ..knowledge.facade import KnowledgeFacade
from ..knowledge.service import KnowledgeService
from ..cache.platform import VersionSnapshot

class ProfileBuilder:
    """
    ProfileBuilder — строит UnifiedDeviceProfile.
    
    Работает ТОЛЬКО через KnowledgeFacade.
    Не знает внутреннюю структуру KnowledgeSnapshot.
    """
    
    def __init__(self, knowledge_service: KnowledgeService):
        self._service = knowledge_service
        self._facade = KnowledgeFacade(knowledge_service)
        
        # Инициализируем Facets с Facade
        self.facets = {
            "summary": SummaryFacet(self._facade),
            "statistics": StatisticsFacet(self._facade),
            "presence": PresenceFacet(self._facade),
            "usage": UsageFacet(self._facade),
            "behaviour": BehaviourFacet(self._facade),
            "mobility": MobilityFacet(self._facade),
            "capability": CapabilityFacet(self._facade)
        }
    
    def build(self, device_id: str, version_snapshot: VersionSnapshot = None) -> UnifiedDeviceProfile:
        """Строит UnifiedDeviceProfile для устройства."""
        if version_snapshot is None:
            version_snapshot = VersionSnapshot()
        
        # Строим Facets через Facade
        facets_data = {}
        for facet_name, facet in self.facets.items():
            facets_data[facet_name] = facet.build(device_id)
        
        # Строим IdentityReference
        summary_data = facets_data.get("summary", {})
        identity = IdentityReference(
            device_uuid=device_id,
            primary_mac=summary_data.get('primary_mac', ''),
            current_ip=summary_data.get('current_ip', ''),
            aliases=tuple(summary_data.get('aliases', [])),
            vendor=summary_data.get('vendor', ''),
            hostname=summary_data.get('hostname', ''),
            device_type=summary_data.get('device_type', ''),
            identity_state=IdentityState.RESOLVED
        )
        
        # Строим Summary
        summary = ProfileSummary(
            known_since=summary_data.get('known_since'),
            last_seen=summary_data.get('last_seen'),
            history_depth=summary_data.get('history_depth', 0),
            sessions=summary_data.get('sessions', 0),
            facts=summary_data.get('facts_count', 0),
            confidence=summary_data.get('average_confidence', 0.0)
        )
        
        # Строим Statistics
        stats_data = facets_data.get("statistics", {})
        statistics = ProfileStatistics(
            facts_total=stats_data.get('facts_total', 0),
            categories_total=len(self._facade.get_categories(device_id)),
            engines_total=len(self._facade.get_engines(device_id)),
            highest_confidence=self._facade.get_highest_confidence(device_id),
            average_confidence=self._facade.get_confidence(device_id),
            timeline_events=stats_data.get('timeline_events', 0),
            sessions=summary.sessions,
            history_depth=summary.history_depth,
            facts_by_engine=self._facade.get_facts_by_engine(device_id),
            facts_by_category=self._facade.get_facts_by_category(device_id),
            capabilities_available=0
        )
        
        # Строим Coverage через Facade
        coverage_data = self._facade.get_coverage(device_id)
        coverage = ProfileCoverage(
            timeline=coverage_data.get('timeline', 0.0),
            metric=coverage_data.get('metric', 0.0),
            feature=coverage_data.get('feature', 0.0),
            rule=coverage_data.get('rule', 0.0),
            fact=coverage_data.get('fact', 0.0),
            knowledge=coverage_data.get('fact', 0.0)
        )
        
        # Строим Confidence
        avg_confidence = self._facade.get_confidence(device_id)
        confidence = ProfileConfidence(
            overall=avg_confidence,
            by_category={},
            by_engine={}
        )
        
        # Строим Categories (ИСПРАВЛЕНО: передаём данные из Facets)
        categories = ProfileCategories(
            presence=facets_data.get("presence", {}),
            usage=facets_data.get("usage", {}),
            behaviour=facets_data.get("behaviour", {}),
            mobility=facets_data.get("mobility", {})
        )
        
        # Создаём immutable Profile (ИСПРАВЛЕНО: передаём _knowledge_service)
        profile = UnifiedDeviceProfile(
            device_id=device_id,
            identity=identity,
            summary=summary,
            categories=categories,
            statistics=statistics,
            coverage=coverage,
            confidence=confidence,
            capabilities={},  # Заполняется позже через CapabilityResolver
            version_snapshot=version_snapshot,
            _knowledge_service=self._service  # ИСПРАВЛЕНО: для Query API
        )
        
        return profile
