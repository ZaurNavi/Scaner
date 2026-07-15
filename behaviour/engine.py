#!/usr/bin/env python3
"""
Behaviour Engine — координация FeatureBuilder, DerivedFeatureCalculator и Evaluator.
"""

from __future__ import annotations

from typing import List, Optional

from .models import BehaviourProfile, FeatureSet, SourceVersions
from .features import FeatureBuilder, DerivedFeatureCalculator
from .evaluator import BehaviourEvaluator
from history import HistoryService
from identity import IdentityService
from session import SessionEngine


class BehaviourEngine:
    """Координирует вычисление признаков и оценку поведения."""
    
    def __init__(
        self,
        history_service: HistoryService,
        identity_service: IdentityService,
        session_engine: Optional[SessionEngine] = None
    ):
        self.feature_builder = FeatureBuilder(history_service, identity_service, session_engine)
        self.derived_calculator = DerivedFeatureCalculator()
        self.evaluator = BehaviourEvaluator()
    
    def analyze(self, device_id: str) -> BehaviourProfile:
        """Анализирует поведение устройства."""
        # Вычисляем сырые признаки
        features = self.feature_builder.build(device_id)
        
        # Вычисляем производные признаки
        features = self.derived_calculator.calculate(features)
        
        # Получаем source_versions
        identity_profile = self.feature_builder.identity.get_identity(device_id)
        source_versions = SourceVersions(
            identity_version=identity_profile.identity_version if identity_profile else 1,
            generated_from_timestamp=identity_profile.last_updated if identity_profile else None
        )
        
        # Применяем правила
        profile = self.evaluator.evaluate(device_id, features, source_versions)
        
        return profile
    
    def analyze_all(self, device_ids: List[str]) -> List[BehaviourProfile]:
        """Анализирует поведение всех устройств."""
        return [self.analyze(device_id) for device_id in device_ids]
