#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
from enum import Enum

class FactStatus(Enum):
    UNKNOWN = "UNKNOWN"; LOW = "LOW"; MEDIUM = "MEDIUM"; HIGH = "HIGH"; CONFIRMED = "CONFIRMED"

@dataclass
class FactExplain:
    timeline_events: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    features: Dict[str, Any] = field(default_factory=dict)
    rules: List[str] = field(default_factory=list)
    confidence_trace: Dict[str, float] = field(default_factory=dict)

@dataclass
class Fact:
    id: str
    engine: str
    category: str
    status: FactStatus
    confidence: float
    quality: float
    sources: List[str]
    matched_rules: List[str]
    matched_features: List[str]
    explain: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
