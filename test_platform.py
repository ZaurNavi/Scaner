#!/usr/bin/env python3
"""
Изолированный тест Scanner Platform Core v1.6.3.
Проверяет ВСЕ компоненты платформы независимо от monitor.py.
"""

import sys
from datetime import datetime
from uuid import uuid4

def main():
    print("=" * 60)
    print("  Scanner Platform Core v1.6.3 — Isolated Test")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # === ТЕСТ 1: Импорт всех компонентов ===
    print("\n📦 ТЕСТ 1: Импорт всех компонентов платформы...")
    try:
        from scanner_platform import (
            Builder, TimelineBuilder, MetricsBuilder, FeaturesBuilder, FactsBuilder,
            ProviderRegistry, ProviderDescriptor,
            MetricRegistry, MetricDescriptor,
            FeatureRegistry, FeatureDescriptor,
            RuleRegistry, RuleDescriptor, RuleCondition, RuleOperator,
            BuilderRegistry, BuilderDescriptor,
            Timeline, TimelineEvent, EventType, TimelineProvider, ProviderResult,
            Fact, FactStatus, FactExplain,
            Pipeline, Coverage, VersionSnapshot, DeviceState, PlatformValidator
        )
        print("   ✅ Все компоненты импортированы успешно")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка импорта: {e}")
        failed += 1
        return 1
    
    # === ТЕСТ 2: PlatformValidator ===
    print("\n🔍 ТЕСТ 2: PlatformValidator...")
    try:
        errors = PlatformValidator.validate_all()
        if errors:
            print(f"   ⚠️  Обнаружены ошибки валидации: {errors}")
            failed += 1
        else:
            print("   ✅ PlatformValidator прошёл успешно")
            passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка валидации: {e}")
        failed += 1
    
    # === ТЕСТ 3: VersionSnapshot ===
    print("\n🔑 ТЕСТ 3: VersionSnapshot и cache key...")
    try:
        snapshot = VersionSnapshot(
            identity="1.0.0", history="1.0.0", session="1.0.0",
            timeline="1.0.0", provider="1.0.0", metric="1.0.0",
            feature="1.0.0", rule="1.0.0", engine="1.0.0"
        )
        cache_key = snapshot.to_cache_key()
        assert len(cache_key) == 9, f"Ожидалось 9 элементов, получено {len(cache_key)}"
        print(f"   ✅ Cache key сформирован: {cache_key[:3]}...")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка VersionSnapshot: {e}")
        failed += 1
    
    # === ТЕСТ 4: Coverage ===
    print("\n📊 ТЕСТ 4: Coverage...")
    try:
        coverage = Coverage(
            timeline_coverage=100.0,
            metric_coverage=85.0,
            feature_coverage=70.0,
            rule_coverage=50.0,
            fact_coverage=30.0
        )
        cov_dict = coverage.to_dict()
        assert "timeline" in cov_dict
        assert cov_dict["timeline"] == 100.0
        print(f"   ✅ Coverage работает: {cov_dict}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Coverage: {e}")
        failed += 1
    
    # === ТЕСТ 5: DeviceState ===
    print("\n📱 ТЕСТ 5: DeviceState...")
    try:
        states = [DeviceState.CONNECTED, DeviceState.ROAMING, DeviceState.IDLE,
                  DeviceState.DISCONNECTED, DeviceState.UNSTABLE]
        assert len(states) == 5
        print(f"   ✅ DeviceState содержит {len(states)} состояний")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка DeviceState: {e}")
        failed += 1
    
    # === ТЕСТ 6: Timeline и TimelineEvent ===
    print("\n⏱️  ТЕСТ 6: Timeline и TimelineEvent...")
    try:
        event1 = TimelineEvent(
            id=str(uuid4()),
            timestamp=datetime.now(),
            device_id="test-device",
            event_type=EventType.CONNECTED,
            source="test_provider",
            payload={"test": "data"},
            quality=0.95,
            confidence=95.0
        )
        event2 = TimelineEvent(
            id=str(uuid4()),
            timestamp=datetime.now(),
            device_id="test-device",
            event_type=EventType.TRAFFIC_SAMPLE,
            source="test_provider",
            payload={"bytes": 1024}
        )
        
        timeline = Timeline(events=[event1, event2], device_id="test-device")
        
        assert timeline.is_immutable() == True
        assert len(timeline.events) == 2
        assert timeline.count_by_type(EventType.CONNECTED) == 1
        assert timeline.count_by_type(EventType.TRAFFIC_SAMPLE) == 1
        
        time_range = timeline.get_time_range()
        assert time_range[0] is not None
        
        print(f"   ✅ Timeline работает: {len(timeline.events)} событий")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Timeline: {e}")
        failed += 1
    
    # === ТЕСТ 7: MetricRegistry ===
    print("\n📈 ТЕСТ 7: MetricRegistry...")
    try:
        # Регистрируем тестовую метрику
        def test_metric_builder(timeline):
            return len(timeline.events)
        
        descriptor = MetricDescriptor(
            id="test_metric",
            builder=test_metric_builder,
            description="Test metric",
            dependencies=["timeline.events"],
            version="1.0.0"
        )
        MetricRegistry.register(descriptor)
        
        # Проверяем регистрацию
        retrieved = MetricRegistry.get("test_metric")
        assert retrieved is not None
        assert retrieved.id == "test_metric"
        
        # Вычисляем метрику из Timeline
        result = MetricRegistry.build(timeline)
        assert "test_metric" in result
        assert result["test_metric"] == 2  # 2 события в timeline
        
        print(f"   ✅ MetricRegistry работает: {result}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка MetricRegistry: {e}")
        failed += 1
    
    # === ТЕСТ 8: FeatureRegistry ===
    print("\n🧩 ТЕСТ 8: FeatureRegistry...")
    try:
        def test_feature_builder(metrics):
            return metrics.get("test_metric", 0) > 0
        
        feature_descriptor = FeatureDescriptor(
            id="test_feature",
            engine="test_engine",
            type=bool,
            builder=test_feature_builder,
            description="Test feature",
            dependencies=["test_metric"],
            version="1.0.0"
        )
        FeatureRegistry.register(feature_descriptor)
        
        # Вычисляем признаки из метрик
        features = FeatureRegistry.build(result)
        assert "test_feature" in features
        assert features["test_feature"] == True
        
        print(f"   ✅ FeatureRegistry работает: {features}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка FeatureRegistry: {e}")
        failed += 1
    
    # === ТЕСТ 9: RuleRegistry ===
    print("\n⚖️  ТЕСТ 9: RuleRegistry...")
    try:
        rule_descriptor = RuleDescriptor(
            id="TEST-RULE-001",
            engine="test_engine",
            name="Test Rule",
            description="Test rule for validation",
            category="test_category",
            expression=[RuleCondition("test_feature", "eq", True)],
            logic=RuleOperator.AND,
            weight=50
        )
        RuleRegistry.register(rule_descriptor)
        
        # Проверяем регистрацию
        rules = RuleRegistry.get_by_engine("test_engine")
        assert "TEST-RULE-001" in rules
        
        enabled = RuleRegistry.get_enabled()
        assert any(r.id == "TEST-RULE-001" for r in enabled)
        
        print(f"   ✅ RuleRegistry работает: {len(rules)} правил для test_engine")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка RuleRegistry: {e}")
        failed += 1
    
    # === ТЕСТ 10: BuilderRegistry ===
    print("\n🏗️  ТЕСТ 10: BuilderRegistry...")
    try:
        BuilderRegistry.register(
            name="test_builder",
            builder_class=TimelineBuilder,
            version="1.0.0",
            dependencies=[]
        )
        
        descriptor = BuilderRegistry.get("test_builder")
        assert descriptor is not None
        assert descriptor.builder_class == TimelineBuilder
        
        print(f"   ✅ BuilderRegistry работает: {descriptor.id}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка BuilderRegistry: {e}")
        failed += 1
    
    # === ТЕСТ 11: TimelineBuilder ===
    print("\n🔨 ТЕСТ 11: TimelineBuilder...")
    try:
        builder = TimelineBuilder()
        assert builder.name == "timeline_builder"
        assert builder.version == "1.0.0"
        
        # Строим пустой timeline (без провайдеров)
        empty_timeline = builder.build("test-device-id")
        assert empty_timeline.device_id == "test-device-id"
        assert len(empty_timeline.events) == 0
        
        print(f"   ✅ TimelineBuilder работает")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка TimelineBuilder: {e}")
        failed += 1
    
    # === ТЕСТ 12: Fact и FactStatus ===
    print("\n🎯 ТЕСТ 12: Fact и FactStatus...")
    try:
        fact = Fact(
            id=str(uuid4()),
            engine="test_engine",
            category="test_category",
            status=FactStatus.HIGH,
            confidence=85.0,
            quality=0.9,
            sources=["test_source"],
            matched_rules=["TEST-RULE-001"],
            matched_features=["test_feature"],
            explain={"test": "explain"}
        )
        
        assert fact.status == FactStatus.HIGH
        assert fact.confidence == 85.0
        assert len(fact.matched_rules) == 1
        
        print(f"   ✅ Fact работает: {fact.category} ({fact.confidence}%)")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Fact: {e}")
        failed += 1
    
    # === ТЕСТ 13: EventType (все типы) ===
    print("\n📋 ТЕСТ 13: EventType (полный список)...")
    try:
        all_types = list(EventType)
        expected_count = 18  # Количество типов событий
        assert len(all_types) >= expected_count, f"Ожидалось {expected_count}+ типов, получено {len(all_types)}"
        
        print(f"   ✅ EventType содержит {len(all_types)} типов событий")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка EventType: {e}")
        failed += 1
    
    # === ИТОГОВАЯ СВОДКА ===
    print("\n" + "=" * 60)
    print(f"📈 ИТОГОВАЯ СВЕРКА:")
    print(f"   ✅ Пройдено тестов: {passed}")
    print(f"   ❌ Провалено тестов: {failed}")
    print(f"   📊 Успешность: {(passed / (passed + failed)) * 100:.1f}%")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 Scanner Platform Core v1.6.3 — ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("   Платформа полностью готова к использованию.")
        return 0
    else:
        print(f"\n⚠️  Обнаружено {failed} проблем. Требуется проверка.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
