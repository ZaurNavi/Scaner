#!/usr/bin/env python3
"""Knowledge Query — декларативный язык запросов через индексы."""
from dataclasses import dataclass, field
from typing import List, Optional, Any, Callable
from datetime import datetime
from .snapshot import KnowledgeSnapshot

@dataclass
class KnowledgeQuery:
    """
    Декларативный запрос к Knowledge Snapshot.
    
    Использует ТОЛЬКО индексы, полный перебор запрещен.
    """
    category: Optional[str] = None
    engine: Optional[str] = None
    status: Optional[str] = None
    confidence_min: Optional[float] = None
    confidence_max: Optional[float] = None
    confidence_range: Optional[tuple] = None  # ДОБАВЛЕНО: (min, max)
    tags: Optional[List[str]] = None
    limit: Optional[int] = None
    sort_by: Optional[str] = None
    predicate: Optional[Callable[[Any], bool]] = None  # ДОБАВЛЕНО: кастомный предикат
    
    def execute(self, snapshot: KnowledgeSnapshot) -> List[Any]:
        """
        Выполняет запрос к Snapshot.
        
        ИСПРАВЛЕНО: использует индексы как стартовую точку,
        а не полный перебор.
        """
        # === ШАГ 1: Определяем стартовый набор через индексы ===
        if self.category:
            # Используем индекс по категории
            results = snapshot.indexes.get_by_category(self.category)
        elif self.engine:
            # Используем индекс по движку
            results = snapshot.indexes.get_by_engine(self.engine)
        elif self.tags and len(self.tags) > 0:
            # Используем индекс по тегам
            tag_results = []
            for tag in self.tags:
                tag_results.extend(snapshot.indexes.get_by_tag(tag))
            results = list(set(tag_results))  # Убираем дубликаты
        else:
            # Если нет фильтров по индексам, берем все ID
            all_ids = snapshot.indexes.get_all_ids()
            results = [snapshot.indexes.get_by_id(fid) for fid in all_ids]
        
        # === ШАГ 2: Дополнительная фильтрация (не полный перебор) ===
        # Фильтрация по статусу
        if self.status:
            results = [f for f in results if hasattr(f, 'status') and f.status.value == self.status]
        
        # Фильтрация по уверенности
        if self.confidence_min is not None:
            results = [f for f in results if f.confidence >= self.confidence_min]
        
        if self.confidence_max is not None:
            results = [f for f in results if f.confidence <= self.confidence_max]
        
        # Фильтрация по confidence_range
        if self.confidence_range:
            min_conf, max_conf = self.confidence_range
            results = [f for f in results if min_conf <= f.confidence <= max_conf]
        
        # Кастомный предикат
        if self.predicate:
            results = [f for f in results if self.predicate(f)]
        
        # === ШАГ 3: Сортировка ===
        if self.sort_by == "confidence":
            results.sort(key=lambda f: f.confidence, reverse=True)
        elif self.sort_by == "timestamp":
            results.sort(
                key=lambda f: f.generated_at if hasattr(f, 'generated_at') else datetime.min,
                reverse=True
            )
        
        # === ШАГ 4: Лимит ===
        if self.limit:
            results = results[:self.limit]
        
        return results
