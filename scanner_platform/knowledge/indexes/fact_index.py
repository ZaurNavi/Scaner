#!/usr/bin/env python3
"""Fact Index — ленивая индексация Platform Facts."""
from typing import Dict, List, Set, Any, Optional
from ..fact_registry import FactRegistry

class FactIndex:
    """
    Ленивый индекс фактов.
    
    Индексы строятся по запросу, а не при создании.
    """
    
    def __init__(self, facts: List[Any]):
        self._facts = facts
        self._by_id: Optional[Dict[str, Any]] = None
        self._by_category: Optional[Dict[str, Set[str]]] = None
        self._by_engine: Optional[Dict[str, Set[str]]] = None
        self._by_tag: Optional[Dict[str, Set[str]]] = None
    
    def _ensure_id_index(self):
        """Ленивая инициализация индекса по ID."""
        if self._by_id is None:
            self._by_id = {fact.id: fact for fact in self._facts}
    
    def _ensure_category_index(self):
        """Ленивая инициализация индекса по категории."""
        if self._by_category is None:
            self._by_category = {}
            for fact in self._facts:
                category = fact.category
                if category not in self._by_category:
                    self._by_category[category] = set()
                self._by_category[category].add(fact.id)
    
    def _ensure_engine_index(self):
        """Ленивая инициализация индекса по движку."""
        if self._by_engine is None:
            self._by_engine = {}
            for fact in self._facts:
                engine = fact.engine
                if engine not in self._by_engine:
                    self._by_engine[engine] = set()
                self._by_engine[engine].add(fact.id)
    
    def _ensure_tag_index(self):
        """Ленивая инициализация индекса по тегам."""
        if self._by_tag is None:
            self._by_tag = {}
            for fact in self._facts:
                # ИСПРАВЛЕНО: используем fact.id, а не fact.category
                descriptor = FactRegistry.get(fact.id)
                if descriptor and descriptor.tags:  # ДОБАВЛЕНО: проверка на None
                    for tag in descriptor.tags:
                        if tag not in self._by_tag:
                            self._by_tag[tag] = set()
                        self._by_tag[tag].add(fact.id)
    
    def get_by_id(self, fact_id: str) -> Any:
        """Получает факт по ID."""
        self._ensure_id_index()
        return self._by_id.get(fact_id)
    
    def get_by_category(self, category: str) -> List[Any]:
        """Получает факты по категории."""
        self._ensure_category_index()
        self._ensure_id_index()  # ИСПРАВЛЕНО: гарантируем наличие _by_id
        fact_ids = self._by_category.get(category, set())
        return [self._by_id[fid] for fid in fact_ids if fid in self._by_id]
    
    def get_by_engine(self, engine: str) -> List[Any]:
        """Получает факты по движку."""
        self._ensure_engine_index()
        self._ensure_id_index()  # ИСПРАВЛЕНО: гарантируем наличие _by_id
        fact_ids = self._by_engine.get(engine, set())
        return [self._by_id[fid] for fid in fact_ids if fid in self._by_id]
    
    def get_by_tag(self, tag: str) -> List[Any]:
        """Получает факты по тегу."""
        self._ensure_tag_index()
        self._ensure_id_index()  # ИСПРАВЛЕНО: гарантируем наличие _by_id
        fact_ids = self._by_tag.get(tag, set())
        return [self._by_id[fid] for fid in fact_ids if fid in self._by_id]
    
    def get_all_ids(self) -> Set[str]:
        """Получает все ID фактов."""
        self._ensure_id_index()
        return set(self._by_id.keys())
