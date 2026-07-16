#!/usr/bin/env python3
"""Rule Descriptors для Behaviour Engine."""
from ...registry.rule_registry import RuleDescriptor, RuleCondition, RuleOperator

BEHAVIOUR_RULES = [
    RuleDescriptor(
        id="BEH-001",
        engine="behaviour",
        name="Office Device",
        description="Офисное устройство: регулярное расписание + всегда онлайн",
        category="office_device",
        expression=[
            RuleCondition("regular_schedule", "eq", True),
            RuleCondition("always_online", "eq", True)
        ],
        logic=RuleOperator.AND,
        weight=60
    ),
    RuleDescriptor(
        id="BEH-002",
        engine="behaviour",
        name="Background Device",
        description="Фоновое устройство: ночная активность + короткие сессии",
        category="background_device",
        expression=[
            RuleCondition("night_user", "eq", True),
            RuleCondition("frequent_short_sessions", "eq", True)
        ],
        logic=RuleOperator.AND,
        weight=55
    ),
    RuleDescriptor(
        id="BEH-003",
        engine="behaviour",
        name="Home Device",
        description="Домашнее устройство: выходные + ночная активность",
        category="home_device",
        expression=[
            RuleCondition("home_pattern", "eq", True),
            RuleCondition("weekend_device", "eq", True)
        ],
        logic=RuleOperator.AND,
        weight=50
    ),
    RuleDescriptor(
        id="BEH-004",
        engine="behaviour",
        name="Rare Visitor",
        description="Редкий посетитель: низкая частота + нерегулярность",
        category="rare_visitor",
        expression=[
            RuleCondition("rare_device", "eq", True),
            RuleCondition("irregular_usage", "eq", True)
        ],
        logic=RuleOperator.AND,
        weight=45
    ),
    RuleDescriptor(
        id="BEH-005",
        engine="behaviour",
        name="Frequent Returner",
        description="Часто возвращающийся: высокая частота + недельная активность",
        category="frequent_returner",
        expression=[
            RuleCondition("frequently_returning", "eq", True),
            RuleCondition("long_sessions", "eq", True)
        ],
        logic=RuleOperator.AND,
        weight=55
    ),
    RuleDescriptor(
        id="BEH-006",
        engine="behaviour",
        name="Night Owl",
        description="Ночная сова: высокая ночная активность",
        category="night_owl",
        expression=[
            RuleCondition("night_user", "eq", True),
            RuleCondition("long_sessions", "eq", True)
        ],
        logic=RuleOperator.AND,
        weight=50
    ),
    RuleDescriptor(
        id="BEH-007",
        engine="behaviour",
        name="Weekend Warrior",
        description="Активен только в выходные",
        category="weekend_warrior",
        expression=[
            RuleCondition("weekend_device", "eq", True),
            RuleCondition("office_pattern", "eq", False)
        ],
        logic=RuleOperator.AND,
        weight=45
    ),
]
