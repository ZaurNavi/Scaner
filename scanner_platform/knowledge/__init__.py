#!/usr/bin/env python3
"""Knowledge Layer — единый слой доступа к знаниям платформы."""

from .service import KnowledgeService
from .cache import KnowledgeCache
from .snapshot import KnowledgeSnapshot
from .query import KnowledgeQuery
from .registry import KnowledgeRegistry, KnowledgeDescriptor, KnowledgeCategory
from .fact_registry import FactRegistry, FactDescriptor, FactSeverity

__all__ = [
    "KnowledgeService",
    "KnowledgeCache",
    "KnowledgeSnapshot",
    "KnowledgeQuery",
    "KnowledgeRegistry",
    "KnowledgeDescriptor",
    "KnowledgeCategory",
    "FactRegistry",
    "FactDescriptor",
    "FactSeverity",
]
