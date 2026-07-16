#!/usr/bin/env python3
"""
Behaviour Engine — тонкий слой поверх BaseEngine.

Движок определяет ТОЛЬКО:
- engine_name
- engine_rules

Всё остальное делает BaseEngine.
"""
from ..core.base_engine import BaseEngine
from .rules.behaviour_rules import BEHAVIOUR_RULES

class BehaviourEngine(BaseEngine):
    """Behaviour Engine на платформенной архитектуре."""
    
    def __init__(self):
        super().__init__(
            engine_name="behaviour",
            engine_rules=BEHAVIOUR_RULES
        )
