#!/usr/bin/env python3
"""RegistryManager — единая точка доступа ко всем Registry."""
from typing import Dict, Any
from .metric_registry import MetricRegistry
from .feature_registry import FeatureRegistry
from .rule_registry import RuleRegistry
from .fact_registry import FactRegistry
from ..knowledge.registry import KnowledgeRegistry
from ..profile.capability.registry import CapabilityRegistry

class RegistryManager:
    """
    Единая точка доступа ко всем Registry платформы.
    
    Внешний код обращается только через RegistryManager.
    """
    
    @classmethod
    def get_metric_registry(cls) -> MetricRegistry:
        """Получает Metric Registry."""
        return MetricRegistry
    
    @classmethod
    def get_feature_registry(cls) -> FeatureRegistry:
        """Получает Feature Registry."""
        return FeatureRegistry
    
    @classmethod
    def get_rule_registry(cls) -> RuleRegistry:
        """Получает Rule Registry."""
        return RuleRegistry
    
    @classmethod
    def get_fact_registry(cls) -> FactRegistry:
        """Получает Fact Registry."""
        return FactRegistry
    
    @classmethod
    def get_knowledge_registry(cls) -> KnowledgeRegistry:
        """Получает Knowledge Registry."""
        return KnowledgeRegistry
    
    @classmethod
    def get_capability_registry(cls) -> CapabilityRegistry:
        """Получает Capability Registry."""
        return CapabilityRegistry
    
    @classmethod
    def get_all_registries(cls) -> Dict[str, Any]:
        """Получает все Registry."""
        return {
            "metric": MetricRegistry,
            "feature": FeatureRegistry,
            "rule": RuleRegistry,
            "fact": FactRegistry,
            "knowledge": KnowledgeRegistry,
            "capability": CapabilityRegistry
        }
