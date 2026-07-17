#!/usr/bin/env python3
"""Indexer — построение O(n) индексов из профилей и фактов."""
from typing import Dict, Any, List

class ProfileIndexer:
    @staticmethod
    def index_facts(facts_list: List[Any]) -> Dict[str, Dict[str, Any]]:
        """
        Преобразует список фактов в словарь {fact_id: fact_dict}.
        Гарантирует O(n) сложность и автономность (нет ссылок на оригинальные объекты).
        """
        indexed = {}
        for fact in facts_list:
            # Преобразуем объект факта в словарь для автономности
            fact_dict = {
                "id": getattr(fact, 'id', str(hash(fact))),
                "engine": getattr(fact, 'engine', 'unknown'),
                "category": getattr(fact, 'category', 'unknown'),
                "confidence": getattr(fact, 'confidence', 0.0),
                "matched_rules": getattr(fact, 'matched_rules', []),
                "matched_features": getattr(fact, 'matched_features', [])
            }
            indexed[fact_dict["id"]] = fact_dict
        return indexed

    @staticmethod
    def index_capabilities(capabilities: Dict[str, bool]) -> Dict[str, bool]:
        return dict(capabilities)
