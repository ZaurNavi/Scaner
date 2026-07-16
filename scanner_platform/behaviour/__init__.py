#!/usr/bin/env python3
"""Behaviour Engine — первый движок на платформенной архитектуре Core."""

from .engine import BehaviourEngine
from .models import EngineResult, EngineStatistics
from .registry import register_all

__all__ = [
    "BehaviourEngine",
    "EngineResult",
    "EngineStatistics",
    "register_all",
]
