#!/usr/bin/env python3
"""Регистрация всех компонентов Behaviour Engine в платформенных Registry."""
from ..registry.metric_registry import MetricRegistry, MetricDescriptor
from ..registry.feature_registry import FeatureRegistry, FeatureDescriptor
from ..registry.rule_registry import RuleRegistry

from .metrics import presence_metrics, activity_metrics, session_metrics
from .features import behaviour_features
from .rules import behaviour_rules

def register_all():
    """Регистрирует все метрики, фичи и правила Behaviour Engine."""
    
    # === МЕТРИКИ ===
    # Presence
    MetricRegistry.register(MetricDescriptor(
        id="daily_presence",
        builder=presence_metrics.build_daily_presence,
        description="Доля дней с активностью",
        dependencies=["timeline.events"],
        version="1.0.0"
    ))
    MetricRegistry.register(MetricDescriptor(
        id="weekly_presence",
        builder=presence_metrics.build_weekly_presence,
        description="Доля недель с активностью",
        dependencies=["timeline.events"],
        version="1.0.0"
    ))
    MetricRegistry.register(MetricDescriptor(
        id="weekend_presence",
        builder=presence_metrics.build_weekend_presence,
        description="Доля активности в выходные",
        dependencies=["timeline.events"],
        version="1.0.0"
    ))
    MetricRegistry.register(MetricDescriptor(
        id="weekday_ratio",
        builder=presence_metrics.build_weekday_ratio,
        description="Доля активности в будни",
        dependencies=["timeline.events"],
        version="1.0.0"
    ))
    
    # Activity
    MetricRegistry.register(MetricDescriptor(
        id="active_hours",
        builder=activity_metrics.build_active_hours,
        description="Общее количество часов активности",
        dependencies=["timeline.events"],
        version="1.0.0"
    ))
    MetricRegistry.register(MetricDescriptor(
        id="night_activity",
        builder=activity_metrics.build_night_activity,
        description="Доля активности в ночное время",
        dependencies=["timeline.events"],
        version="1.0.0"
    ))
    MetricRegistry.register(MetricDescriptor(
        id="office_hours_activity",
        builder=activity_metrics.build_office_hours_activity,
        description="Доля активности в рабочие часы",
        dependencies=["timeline.events"],
        version="1.0.0"
    ))
    
    # Session
    MetricRegistry.register(MetricDescriptor(
        id="appearance_frequency",
        builder=session_metrics.build_appearance_frequency,
        description="Количество появлений устройства",
        dependencies=["timeline.session_started"],
        version="1.0.0"
    ))
    MetricRegistry.register(MetricDescriptor(
        id="online_duration",
        builder=session_metrics.build_online_duration,
        description="Общая продолжительность онлайн (сек)",
        dependencies=["timeline.events"],
        version="1.0.0"
    ))
    MetricRegistry.register(MetricDescriptor(
        id="idle_duration",
        builder=session_metrics.build_idle_duration,
        description="Доля времени без активности",
        dependencies=["timeline.events"],
        version="1.0.0"
    ))
    
    # === ФИЧИ ===
    features = [
        ("regular_schedule", bool, behaviour_features.build_regular_schedule, 
         ["daily_presence", "weekday_ratio", "office_hours_activity"], "Регулярное расписание"),
        ("night_user", bool, behaviour_features.build_night_user,
         ["night_activity"], "Ночной пользователь"),
        ("weekend_device", bool, behaviour_features.build_weekend_device,
         ["weekend_presence"], "Устройство выходного дня"),
        ("office_pattern", bool, behaviour_features.build_office_pattern,
         ["office_hours_activity", "weekday_ratio"], "Офисный паттерн"),
        ("home_pattern", bool, behaviour_features.build_home_pattern,
         ["weekend_presence", "night_activity"], "Домашний паттерн"),
        ("frequent_short_sessions", bool, behaviour_features.build_frequent_short_sessions,
         ["appearance_frequency", "idle_duration"], "Частые короткие сессии"),
        ("long_sessions", bool, behaviour_features.build_long_sessions,
         ["online_duration"], "Длинные сессии"),
        ("irregular_usage", bool, behaviour_features.build_irregular_usage,
         ["daily_presence", "weekly_presence"], "Нерегулярное использование"),
        ("rare_device", bool, behaviour_features.build_rare_device,
         ["appearance_frequency", "daily_presence"], "Редкое устройство"),
        ("always_online", bool, behaviour_features.build_always_online,
         ["daily_presence", "idle_duration"], "Постоянно онлайн"),
        ("frequently_returning", bool, behaviour_features.build_frequently_returning,
         ["appearance_frequency", "weekly_presence"], "Часто возвращающийся"),
    ]
    
    for feat_id, feat_type, builder, deps, desc in features:
        FeatureRegistry.register(FeatureDescriptor(
            id=feat_id,
            engine="behaviour",
            type=feat_type,
            builder=builder,
            description=desc,
            dependencies=deps,
            version="1.0.0"
        ))
    
    # === ПРАВИЛА ===
    for rule in behaviour_rules.BEHAVIOUR_RULES:
        RuleRegistry.register(rule)
