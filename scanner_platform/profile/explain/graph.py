#!/usr/bin/env python3
"""Explain Graph — граф объяснений."""
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass(frozen=True)
class ExplainGraph:
    """
    Граф объяснений (immutable).
    
    Строится через ExplainService.build(profile).
    """
    device_id: str
    facts_count: int
    categories: List[str]
    engines: List[str]
    confidence_trace: Dict[str, float] = field(default_factory=dict)
