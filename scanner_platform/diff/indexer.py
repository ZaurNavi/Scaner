#!/usr/bin/env python3
"""ProfileIndexer — O(n) извлечение данных строго из UnifiedDeviceProfile."""
from typing import Dict, Any, Tuple
from types import MappingProxyType
from ..profile import UnifiedDeviceProfile
from .enums import CapabilityState

class ProfileIndexer:
    @staticmethod
    def index_facts(profile: UnifiedDeviceProfile) -> Dict[str, Dict[str, Any]]:
        """
        Извлекает факты через Query API профиля.
        Возвращает словарь {fact_id: fact_dict} для O(n) сравнения.
        """
        indexed = {}
        # Используем публичный API профиля, не залезая во внутренности
        facts = profile.query().all()
        for fact in facts:
            fact_dict = {
                "id": getattr(fact, 'id', str(hash(fact))),
                "engine": getattr(fact, 'engine', 'unknown'),
                "category": getattr(fact, 'category', 'unknown'),
                "confidence": getattr(fact, 'confidence', 0.0),
                "matched_rules": tuple(getattr(fact, 'matched_rules', [])),
                "matched_features": tuple(getattr(fact, 'matched_features', []))
            }
            indexed[fact_dict["id"]] = fact_dict
        return indexed

    @staticmethod
    def index_engines(profile: UnifiedDeviceProfile) -> Tuple[str, ...]:
        """Извлекает уникальные движки из статистики профиля."""
        engines = set()
        stats = profile.statistics
        if hasattr(stats, 'facts_by_engine') and isinstance(stats.facts_by_engine, dict):
            engines.update(stats.facts_by_engine.keys())
        return tuple(sorted(engines))

    @staticmethod
    def index_capabilities(profile: UnifiedDeviceProfile) -> Dict[str, CapabilityState]:
        """Индексирует возможности и их состояние."""
        caps = {}
        for cap_name, is_available in profile.capabilities.items():
            # Упрощенная логика: если доступно - AVAILABLE, иначе NOT_AVAILABLE
            # В будущем можно добавить PARTIAL на основе метаданных
            state = CapabilityState.AVAILABLE if is_available else CapabilityState.NOT_AVAILABLE
            caps[cap_name] = state
        return caps
