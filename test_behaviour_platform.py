#!/usr/bin/env python3
"""
Изолированный тест Behaviour Engine на платформенной архитектуре v1.6.4.
Проверяет BaseEngine, PlatformContext, Bundles и полный pipeline.
"""

import sys
from datetime import datetime
from uuid import uuid4

def main():
    print("=" * 70)
    print("  Behaviour Engine v1.6.4 — Platform Architecture Test")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    # === ТЕСТ 1: Импорт всех компонентов ===
    print("\n📦 ТЕСТ 1: Импорт компонентов Platform Core...")
    try:
        from scanner_platform.core.bundles import MetricBundle, FeatureBundle, RuleBundle
        from scanner_platform.core.platform_context import PlatformContext
        from scanner_platform.core.base_engine import BaseEngine, EngineResult
        from scanner_platform.core.platform import Platform
        from scanner_platform.behaviour.engine import BehaviourEngine
        from scanner_platform.timeline.models import Timeline, TimelineEvent, EventType
        print("   ✅ Все компоненты импортированы")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
        return 1
    
    # === ТЕСТ 2: Bundles ===
    print("\n📦 ТЕСТ 2: MetricBundle, FeatureBundle, RuleBundle...")
    try:
        metric_bundle = MetricBundle(
            metrics={"daily_presence": 0.8, "active_hours": 12.5},
            version="1.0.0"
        )
        assert metric_bundle.get("daily_presence") == 0.8
        assert "active_hours" in metric_bundle
        
        feature_bundle = FeatureBundle(
            features={"regular_schedule": True, "night_user": False},
            version="1.0.0"
        )
        assert feature_bundle.get("regular_schedule") == True
        
        rule_bundle = RuleBundle(rules=[], version="1.0.0")
        
        print(f"   ✅ Bundles работают: {len(metric_bundle.metrics)} метрик, {len(feature_bundle.features)} фич")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Bundles: {e}")
        failed += 1
    
    # === ТЕСТ 3: PlatformContext ===
    print("\n🔗 ТЕСТ 3: PlatformContext...")
    try:
        # Создаём тестовый Timeline
        event = TimelineEvent(
            id=str(uuid4()),
            timestamp=datetime.now(),
            device_id="test-device",
            event_type=EventType.SESSION_STARTED,
            source="test"
        )
        timeline = Timeline(events=[event], device_id="test-device")
        
        context = PlatformContext(
            device_id="test-device",
            timeline=timeline,
            metrics=metric_bundle,
            features=feature_bundle,
            rules=rule_bundle
        )
        
        assert context.device_id == "test-device"
        assert context.metrics.get("daily_presence") == 0.8
        assert context.features.get("regular_schedule") == True
        
        print(f"   ✅ PlatformContext работает")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка PlatformContext: {e}")
        failed += 1
    
    # === ТЕСТ 4: BaseEngine ===
    print("\n🏗️  ТЕСТ 4: BaseEngine (базовый класс)...")
    try:
        # BaseEngine — абстрактный, создаём тестовый
        from scanner_platform.registry.rule_registry import RuleDescriptor, RuleCondition, RuleOperator
        
        class TestEngine(BaseEngine):
            def __init__(self):
                test_rules = [
                    RuleDescriptor(
                        id="TEST-001",
                        engine="test",
                        name="Test Rule",
                        description="Test",
                        category="test_category",
                        expression=[RuleCondition("regular_schedule", "eq", True)],
                        logic=RuleOperator.AND,
                        weight=50
                    )
                ]
                super().__init__(engine_name="test", engine_rules=test_rules)
        
        test_engine = TestEngine()
        assert test_engine.engine_name == "test"
        assert len(test_engine.engine_rules) == 1
        
        print(f"   ✅ BaseEngine работает")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка BaseEngine: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    
    # === ТЕСТ 5: BehaviourEngine ===
    print("\n🧠 ТЕСТ 5: BehaviourEngine (наследник BaseEngine)...")
    try:
        behaviour_engine = BehaviourEngine()
        assert behaviour_engine.engine_name == "behaviour"
        assert len(behaviour_engine.engine_rules) > 0, "Должны быть правила"
        
        print(f"   ✅ BehaviourEngine работает: {len(behaviour_engine.engine_rules)} правил")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка BehaviourEngine: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    
    # === ТЕСТ 6: Полный pipeline ===
    print("\n🔄 ТЕСТ 6: Полный pipeline (BaseEngine.run)...")
    try:
        # Создаём контекст с реальными фичами
        test_features = {
            "regular_schedule": True,
            "always_online": True,
            "night_user": False,
            "weekend_device": False
        }
        
        test_context = PlatformContext(
            device_id="test-device-123",
            timeline=timeline,
            metrics=MetricBundle(metrics={}),
            features=FeatureBundle(features=test_features),
            rules=RuleBundle(rules=[])
        )
        
        # Запускаем BehaviourEngine
        result = behaviour_engine.run(test_context)
        
        assert result is not None
        assert result.engine == "behaviour"
        assert result.device_id == "test-device-123"
        assert hasattr(result, 'facts')
        assert hasattr(result, 'coverage')
        assert hasattr(result, 'statistics')
        assert hasattr(result, 'explain')
        assert hasattr(result, 'dependencies')
        
        print(f"   ✅ Pipeline работает:")
        print(f"      • Facts: {len(result.facts)}")
        print(f"      • Coverage: rule={result.coverage.rule_coverage:.1f}%, fact={result.coverage.fact_coverage:.1f}%")
        print(f"      • Statistics: {result.statistics}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка pipeline: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    
    # === ТЕСТ 7: EngineResult ===
    print("\n📊 ТЕСТ 7: EngineResult структура...")
    try:
        assert result.version == "1.0.0"
        assert result.version_snapshot is not None
        assert result.version_snapshot.engine_version == "1.0.0"
        assert "timeline_version" in result.dependencies
        assert "metric_version" in result.dependencies
        
        print(f"   ✅ EngineResult имеет все поля:")
        print(f"      • version: {result.version}")
        print(f"      • dependencies: {list(result.dependencies.keys())}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка EngineResult: {e}")
        failed += 1
    
    # === ТЕСТ 8: Coverage в BaseEngine ===
    print("\n📈 ТЕСТ 8: Coverage вычисляется в BaseEngine...")
    try:
        assert result.coverage.timeline_coverage == 100.0
        assert result.coverage.metric_coverage == 100.0
        assert result.coverage.feature_coverage == 100.0
        assert 0 <= result.coverage.rule_coverage <= 100
        assert 0 <= result.coverage.fact_coverage <= 100
        
        print(f"   ✅ Coverage корректный: {result.coverage.to_dict()}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Coverage: {e}")
        failed += 1
    
    # === ТЕСТ 9: Explain в BaseEngine ===
    print("\n🔍 ТЕСТ 9: Explain вычисляется в BaseEngine...")
    try:
        assert "engine" in result.explain
        assert result.explain["engine"] == "behaviour"
        assert "facts" in result.explain
        
        print(f"   ✅ Explain корректный: engine={result.explain['engine']}, facts={len(result.explain['facts'])}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Explain: {e}")
        failed += 1
    
    # === ТЕСТ 10: Кэширование ===
    print("\n💾 ТЕСТ 10: Кэширование в BaseEngine...")
    try:
        # Первый запуск
        result1 = behaviour_engine.run(test_context)
        time1 = result1.statistics["computation_time_ms"]
        
        # Второй запуск (должен быть из кэша)
        result2 = behaviour_engine.run(test_context)
        time2 = result2.statistics["computation_time_ms"]
        
        assert time2 == 0.0, "Второй запуск должен быть из кэша (0ms)"
        
        print(f"   ✅ Кэширование работает: первый={time1:.2f}ms, второй={time2:.2f}ms")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка кэширования: {e}")
        failed += 1
    
    # === ИТОГОВАЯ СВОДКА ===
    print("\n" + "=" * 70)
    print(f"📈 ИТОГОВАЯ СВЕРКА:")
    print(f"   ✅ Пройдено тестов: {passed}")
    print(f"   ❌ Провалено тестов: {failed}")
    print(f"   📊 Успешность: {(passed / (passed + failed)) * 100:.1f}%")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 Behaviour Engine v1.6.4 — ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("   Platform Core архитектура полностью готова.")
        print("   Можно коммитить!")
        return 0
    else:
        print(f"\n⚠️  Обнаружено {failed} проблем. Требуется исправление.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
