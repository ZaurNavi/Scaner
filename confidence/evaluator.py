#!/usr/bin/env python3
"""
Evaluator — главный исполнитель оценки достоверности.
Получает Identity Profile, применяет правила, формирует оценки.

v1.6.9.5: Принимает ConfidenceRules через конструктор (Dependency Injection).
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Optional

from .categories import FactCategory
from .models import (
    FactAssessment, FactStatus, ConfidenceProfile,
    ConfidenceSummary, ConfidenceStatistics
)
from .rules import ConfidenceRules
from .normalizer import normalize_score

# v1.6.9.5: Configuration Layer Integration
from configuration import ConfigurationManager


class ConfidenceEvaluator:
    """Оценщик достоверности фактов."""
    
    def __init__(
        self,
        rules: Optional[ConfidenceRules] = None,
        configuration: Optional[ConfigurationManager] = None
    ):
        """
        v1.6.9.5: Конструктор с Dependency Injection.
        
        Args:
            rules: Сервис правил (если None — создаётся автоматически)
            configuration: Конфигурация (используется если rules=None)
        """
        if rules is not None:
            self.rules = rules
        elif configuration is not None:
            # Создаём ConfidenceRules с переданной конфигурацией
            self.rules = ConfidenceRules(configuration)
        else:
            # Fallback: используем глобальный Singleton (для обратной совместимости)
            from configuration import get_config_manager
            self.rules = ConfidenceRules(get_config_manager())
    
    def evaluate(self, identity_profile) -> ConfidenceProfile:
        """
        Оценивает все факты в Identity Profile.
        
        Args:
            identity_profile: IdentityProfile из Identity Service
        
        Returns:
            ConfidenceProfile с оценками всех фактов
        """
        profile = ConfidenceProfile(
            identity_id=identity_profile.identity_id,
            generated_at=datetime.now()
        )
        
        # Оцениваем каждую категорию
        profile.facts[FactCategory.VENDOR] = self._evaluate_vendors(identity_profile)
        profile.facts[FactCategory.MODEL] = self._evaluate_models(identity_profile)
        profile.facts[FactCategory.HOSTNAME] = self._evaluate_hostnames(identity_profile)
        profile.facts[FactCategory.OS] = self._evaluate_operating_systems(identity_profile)
        profile.facts[FactCategory.DEVICE_TYPE] = self._evaluate_device_types(identity_profile)
        profile.facts[FactCategory.SSID] = self._evaluate_ssids(identity_profile)
        profile.facts[FactCategory.ACCESS_POINT] = self._evaluate_access_points(identity_profile)
        profile.facts[FactCategory.VLAN] = self._evaluate_vlans(identity_profile)
        profile.facts[FactCategory.RADIO] = self._evaluate_radios(identity_profile)
        profile.facts[FactCategory.WIFI_CAPABILITY] = self._evaluate_wifi_capabilities(identity_profile)
        
        # Формируем summary (лучшие оценки)
        profile.summary = self._build_summary(profile.facts)
        
        # Вычисляем coverage
        profile.coverage = self._calculate_coverage(profile.facts)
        
        # Вычисляем statistics
        profile.statistics = self._calculate_statistics(profile.facts)
        
        return profile
    
    def _evaluate_vendors(self, identity_profile) -> List[FactAssessment]:
        """Оценивает vendors."""
        assessments = []
        vendor_sources = {}  # value -> {source: weight}
        
        for vendor_attr in identity_profile.device.known_vendors:
            value = vendor_attr.value
            if value not in vendor_sources:
                vendor_sources[value] = {}
            
            for source in vendor_attr.sources:
                weight = self.rules.get_weight(FactCategory.VENDOR, source)
                if weight > 0:
                    vendor_sources[value][source] = weight
        
        for value, sources in vendor_sources.items():
            raw_score = sum(sources.values())
            confidence = normalize_score(raw_score)
            
            assessments.append(FactAssessment(
                category=FactCategory.VENDOR,
                value=value,
                raw_score=raw_score,
                confidence=confidence,
                status=FactStatus.EVALUATED,
                sources=list(sources.keys()),
                reasons=[f"+{w} {s}" for s, w in sources.items()],
                evidence=[{"source": s, "weight": w} for s, w in sources.items()]
            ))
        
        return assessments
    
    def _evaluate_models(self, identity_profile) -> List[FactAssessment]:
        """Оценивает models."""
        assessments = []
        model_sources = {}
        
        for model_attr in identity_profile.device.known_models:
            value = model_attr.value
            if value not in model_sources:
                model_sources[value] = {}
            
            for source in model_attr.sources:
                weight = self.rules.get_weight(FactCategory.MODEL, source)
                if weight > 0:
                    model_sources[value][source] = weight
        
        for value, sources in model_sources.items():
            raw_score = sum(sources.values())
            confidence = normalize_score(raw_score)
            
            assessments.append(FactAssessment(
                category=FactCategory.MODEL,
                value=value,
                raw_score=raw_score,
                confidence=confidence,
                status=FactStatus.EVALUATED,
                sources=list(sources.keys()),
                reasons=[f"+{w} {s}" for s, w in sources.items()],
                evidence=[{"source": s, "weight": w} for s, w in sources.items()]
            ))
        
        return assessments
    
    def _evaluate_hostnames(self, identity_profile) -> List[FactAssessment]:
        """Оценивает hostnames."""
        assessments = []
        hostname_sources = {}
        
        for hostname_attr in identity_profile.device.known_hostnames:
            value = hostname_attr.value
            if value not in hostname_sources:
                hostname_sources[value] = {}
            
            for source in hostname_attr.sources:
                weight = self.rules.get_weight(FactCategory.HOSTNAME, source)
                if weight > 0:
                    hostname_sources[value][source] = weight
        
        for value, sources in hostname_sources.items():
            raw_score = sum(sources.values())
            confidence = normalize_score(raw_score)
            
            assessments.append(FactAssessment(
                category=FactCategory.HOSTNAME,
                value=value,
                raw_score=raw_score,
                confidence=confidence,
                status=FactStatus.EVALUATED,
                sources=list(sources.keys()),
                reasons=[f"+{w} {s}" for s, w in sources.items()],
                evidence=[{"source": s, "weight": w} for s, w in sources.items()]
            ))
        
        return assessments
    
    def _evaluate_operating_systems(self, identity_profile) -> List[FactAssessment]:
        """Оценивает operating systems."""
        assessments = []
        os_sources = {}
        
        for os_attr in identity_profile.device.known_operating_systems:
            value = os_attr.value
            if value not in os_sources:
                os_sources[value] = {}
            
            for source in os_attr.sources:
                weight = self.rules.get_weight(FactCategory.OS, source)
                if weight > 0:
                    os_sources[value][source] = weight
        
        for value, sources in os_sources.items():
            raw_score = sum(sources.values())
            confidence = normalize_score(raw_score)
            
            assessments.append(FactAssessment(
                category=FactCategory.OS,
                value=value,
                raw_score=raw_score,
                confidence=confidence,
                status=FactStatus.EVALUATED,
                sources=list(sources.keys()),
                reasons=[f"+{w} {s}" for s, w in sources.items()],
                evidence=[{"source": s, "weight": w} for s, w in sources.items()]
            ))
        
        return assessments
    
    def _evaluate_device_types(self, identity_profile) -> List[FactAssessment]:
        """Оценивает device types."""
        assessments = []
        type_sources = {}
        
        for type_attr in identity_profile.device.known_device_types:
            value = type_attr.value
            if value not in type_sources:
                type_sources[value] = {}
            
            for source in type_attr.sources:
                weight = self.rules.get_weight(FactCategory.DEVICE_TYPE, source)
                if weight > 0:
                    type_sources[value][source] = weight
        
        for value, sources in type_sources.items():
            raw_score = sum(sources.values())
            confidence = normalize_score(raw_score)
            
            assessments.append(FactAssessment(
                category=FactCategory.DEVICE_TYPE,
                value=value,
                raw_score=raw_score,
                confidence=confidence,
                status=FactStatus.EVALUATED,
                sources=list(sources.keys()),
                reasons=[f"+{w} {s}" for s, w in sources.items()],
                evidence=[{"source": s, "weight": w} for s, w in sources.items()]
            ))
        
        return assessments
    
    def _evaluate_ssids(self, identity_profile) -> List[FactAssessment]:
        """Оценивает SSIDs."""
        assessments = []
        ssid_sources = {}
        
        for ssid_attr in identity_profile.network.known_ssids:
            value = ssid_attr.value
            if value not in ssid_sources:
                ssid_sources[value] = {}
            
            for source in ssid_attr.sources:
                weight = self.rules.get_weight(FactCategory.SSID, source)
                if weight > 0:
                    ssid_sources[value][source] = weight
        
        for value, sources in ssid_sources.items():
            raw_score = sum(sources.values())
            confidence = normalize_score(raw_score)
            
            assessments.append(FactAssessment(
                category=FactCategory.SSID,
                value=value,
                raw_score=raw_score,
                confidence=confidence,
                status=FactStatus.EVALUATED,
                sources=list(sources.keys()),
                reasons=[f"+{w} {s}" for s, w in sources.items()],
                evidence=[{"source": s, "weight": w} for s, w in sources.items()]
            ))
        
        return assessments
    
    def _evaluate_access_points(self, identity_profile) -> List[FactAssessment]:
        """Оценивает access points."""
        assessments = []
        ap_sources = {}
        
        for ap_attr in identity_profile.network.known_aps:
            value = ap_attr.value
            if value not in ap_sources:
                ap_sources[value] = {}
            
            for source in ap_attr.sources:
                weight = self.rules.get_weight(FactCategory.ACCESS_POINT, source)
                if weight > 0:
                    ap_sources[value][source] = weight
        
        for value, sources in ap_sources.items():
            raw_score = sum(sources.values())
            confidence = normalize_score(raw_score)
            
            assessments.append(FactAssessment(
                category=FactCategory.ACCESS_POINT,
                value=value,
                raw_score=raw_score,
                confidence=confidence,
                status=FactStatus.EVALUATED,
                sources=list(sources.keys()),
                reasons=[f"+{w} {s}" for s, w in sources.items()],
                evidence=[{"source": s, "weight": w} for s, w in sources.items()]
            ))
        
        return assessments
    
    def _evaluate_vlans(self, identity_profile) -> List[FactAssessment]:
        """Оценивает VLANs."""
        assessments = []
        vlan_sources = {}
        
        for vlan_attr in identity_profile.network.known_vlans:
            value = vlan_attr.value
            if value not in vlan_sources:
                vlan_sources[value] = {}
            
            for source in vlan_attr.sources:
                weight = self.rules.get_weight(FactCategory.VLAN, source)
                if weight > 0:
                    vlan_sources[value][source] = weight
        
        for value, sources in vlan_sources.items():
            raw_score = sum(sources.values())
            confidence = normalize_score(raw_score)
            
            assessments.append(FactAssessment(
                category=FactCategory.VLAN,
                value=value,
                raw_score=raw_score,
                confidence=confidence,
                status=FactStatus.EVALUATED,
                sources=list(sources.keys()),
                reasons=[f"+{w} {s}" for s, w in sources.items()],
                evidence=[{"source": s, "weight": w} for s, w in sources.items()]
            ))
        
        return assessments
    
    def _evaluate_radios(self, identity_profile) -> List[FactAssessment]:
        """Оценивает radios."""
        assessments = []
        radio_sources = {}
        
        for radio_attr in identity_profile.network.known_radios:
            value = radio_attr.value
            if value not in radio_sources:
                radio_sources[value] = {}
            
            for source in radio_attr.sources:
                weight = self.rules.get_weight(FactCategory.RADIO, source)
                if weight > 0:
                    radio_sources[value][source] = weight
        
        for value, sources in radio_sources.items():
            raw_score = sum(sources.values())
            confidence = normalize_score(raw_score)
            
            assessments.append(FactAssessment(
                category=FactCategory.RADIO,
                value=value,
                raw_score=raw_score,
                confidence=confidence,
                status=FactStatus.EVALUATED,
                sources=list(sources.keys()),
                reasons=[f"+{w} {s}" for s, w in sources.items()],
                evidence=[{"source": s, "weight": w} for s, w in sources.items()]
            ))
        
        return assessments
    
    def _evaluate_wifi_capabilities(self, identity_profile) -> List[FactAssessment]:
        """Оценивает wifi capabilities."""
        assessments = []
        wifi_sources = {}
        
        for wifi_attr in identity_profile.network.known_wifi_capabilities:
            value = wifi_attr.value
            if value not in wifi_sources:
                wifi_sources[value] = {}
            
            for source in wifi_attr.sources:
                weight = self.rules.get_weight(FactCategory.WIFI_CAPABILITY, source)
                if weight > 0:
                    wifi_sources[value][source] = weight
        
        for value, sources in wifi_sources.items():
            raw_score = sum(sources.values())
            confidence = normalize_score(raw_score)
            
            assessments.append(FactAssessment(
                category=FactCategory.WIFI_CAPABILITY,
                value=value,
                raw_score=raw_score,
                confidence=confidence,
                status=FactStatus.EVALUATED,
                sources=list(sources.keys()),
                reasons=[f"+{w} {s}" for s, w in sources.items()],
                evidence=[{"source": s, "weight": w} for s, w in sources.items()]
            ))
        
        return assessments
    
    def _build_summary(self, facts: Dict[FactCategory, List[FactAssessment]]) -> ConfidenceSummary:
        """Формирует summary с лучшими оценками."""
        summary = ConfidenceSummary()
        
        if FactCategory.VENDOR in facts and facts[FactCategory.VENDOR]:
            summary.vendor = max(facts[FactCategory.VENDOR], key=lambda x: x.confidence)
        
        if FactCategory.MODEL in facts and facts[FactCategory.MODEL]:
            summary.model = max(facts[FactCategory.MODEL], key=lambda x: x.confidence)
        
        if FactCategory.HOSTNAME in facts and facts[FactCategory.HOSTNAME]:
            summary.hostname = max(facts[FactCategory.HOSTNAME], key=lambda x: x.confidence)
        
        if FactCategory.OS in facts and facts[FactCategory.OS]:
            summary.os = max(facts[FactCategory.OS], key=lambda x: x.confidence)
        
        if FactCategory.DEVICE_TYPE in facts and facts[FactCategory.DEVICE_TYPE]:
            summary.device_type = max(facts[FactCategory.DEVICE_TYPE], key=lambda x: x.confidence)
        
        return summary
    
    def _calculate_coverage(self, facts: Dict[FactCategory, List[FactAssessment]]) -> float:
        """Вычисляет покрытие (полноту знаний)."""
        total_categories = len(FactCategory)
        filled_categories = sum(1 for cat in FactCategory if cat in facts and facts[cat])
        return (filled_categories / total_categories) * 100.0 if total_categories > 0 else 0.0
    
    def _calculate_statistics(self, facts: Dict[FactCategory, List[FactAssessment]]) -> ConfidenceStatistics:
        """Вычисляет статистику оценок."""
        stats = ConfidenceStatistics()
        
        for category, assessments in facts.items():
            for assessment in assessments:
                stats.total_facts += 1
                
                if assessment.status == FactStatus.EVALUATED:
                    stats.evaluated += 1
                elif assessment.status == FactStatus.CONFLICT:
                    stats.conflicts += 1
                elif assessment.status == FactStatus.INSUFFICIENT_DATA:
                    stats.insufficient_data += 1
                else:
                    stats.unknown += 1
        
        return stats
