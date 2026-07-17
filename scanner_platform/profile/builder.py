#!/usr/bin/env python3
"""ProfileBuilder — строит UnifiedDeviceProfile."""
import time
from datetime import datetime
from typing import Dict, Any
from .profile import UnifiedDeviceProfile
from .models import ProfileSummary, ProfileStatistics, ProfileCoverage, ProfileConfidence, IdentityState
from .facets.summary import SummaryFacet
from .facets.statistics import StatisticsFacet
from .facets.presence import PresenceFacet
from .facets.usage import UsageFacet
from .facets.behaviour import BehaviourFacet
from .facets.mobility import MobilityFacet
from .facets.capability import CapabilityFacet
from .capability.resolver import CapabilityResolver
from ..knowledge.service import KnowledgeService
from ..cache.platform import VersionSnapshot

class ProfileBuilder:
    """
    ProfileBuilder — строит UnifiedDeviceProfile.
    
    Работает ТОЛЬКО через KnowledgeService.
    Не знает внутреннюю структуру KnowledgeSnapshot.
    """
    
    def __init__(self, knowledge_service: KnowledgeService):
        self.knowledge_service = knowledge_service
        
        # Инициализируем Facets
        self.facets = {
            "summary": SummaryFacet(knowledge_service),
            "statistics": StatisticsFacet(knowledge_service),
            "presence": PresenceFacet(knowledge_service),
            "usage": UsageFacet(knowledge_service),
            "behaviour": BehaviourFacet(knowledge_service),
            "mobility": MobilityFacet(knowledge_service),
            "capability": CapabilityFacet(knowledge_service)
        }
    
    def build(self, device_id: str, version_snapshot: VersionSnapshot = None) -> UnifiedDeviceProfile:
        """
        Строит UnifiedDeviceProfile для устройства.
        
        Args:
            device_id: Идентификатор устройства
            version_snapshot: Версии компонентов
        
        Returns:
            UnifiedDeviceProfile (immutable)
        """
        if version_snapshot is None:
            version_snapshot = VersionSnapshot()
        
        # Получаем Snapshot через KnowledgeService
        snapshot = self.knowledge_service.get_snapshot(device_id)
        if not snapshot:
            raise ValueError(f"No Knowledge Snapshot found for device {device_id}")
        
        # Строим Facets
        facets_data = {}
        for facet_name, facet in self.facets.items():
            facets_data[facet_name] = facet.build(device_id)
        
        # Строим Summary
        summary_data = facets_data.get("summary", {})
        summary = ProfileSummary(
            known_since=summary_data.get('known_since'),
            last_seen=summary_data.get('last_seen'),
            history_depth=summary_data.get('history_depth', 0),
            sessions=summary_data.get('sessions', 0),
            facts=summary_data.get('facts_count', 0),
            confidence=summary_data.get('average_confidence', 0.0),
            vendor=summary_data.get('vendor', ''),
            hostname=summary_data.get('hostname', ''),
            device_type=summary_data.get('device_type', ''),
            identity_state=IdentityState.RESOLVED
        )
        
        # Строим Statistics
        stats_data = facets_data.get("statistics", {})
        cap_data = facets_data.get("capability", {})
        statistics = ProfileStatistics(
            facts_total=stats_data.get('facts_total', 0),
            categories_total=len(set(f.category for f in snapshot.facts)) if snapshot.facts else 0,
            engines_total=len(set(f.engine for f in snapshot.facts)) if snapshot.facts else 0,
            highest_confidence=stats_data.get('highest_confidence', 0.0),
            average_confidence=stats_data.get('average_confidence', 0.0),
            timeline_events=len(snapshot.indexes.get_all_ids()) if snapshot.indexes else 0,
            sessions=summary.sessions,
            history_depth=summary.history_depth,
            facts_by_engine=stats_data.get('facts_by_engine', {}),
            facts_by_category=stats_data.get('facts_by_category', {}),
            capabilities_available=cap_data.get('available', 0)
        )
        
        # Строим Coverage (агрегируем из Knowledge)
        coverage = ProfileCoverage(
            timeline=snapshot.coverage.timeline_coverage,
            metric=snapshot.coverage.metric_coverage,
            feature=snapshot.coverage.feature_coverage,
            rule=snapshot.coverage.rule_coverage,
            fact=snapshot.coverage.fact_coverage,
            knowledge=snapshot.coverage.fact_coverage
        )
        
        # Строим Confidence
        avg_confidence = sum(f.confidence for f in snapshot.facts) / len(snapshot.facts) if snapshot.facts else 0.0
        confidence = ProfileConfidence(
            overall=avg_confidence,
            by_category={},  # Можно расширить
            by_engine={}     # Можно расширить
        )
        
        # Определяем Capabilities
        capabilities = CapabilityResolver.resolve(snapshot)
        
        # Создаём immutable Profile
        profile = UnifiedDeviceProfile(
            device_id=device_id,
            identity={},  # Можно расширить
            summary=summary,
            categories=facets_data,
            statistics=statistics,
            coverage=coverage,
            confidence=confidence,
            capabilities=capabilities,
            version_snapshot=version_snapshot,
            _snapshot=snapshot
        )
        
        return profile
