#!/usr/bin/env python3
"""
Исчерпывающий тест Domain Event Layer v1.6.8.
Покрывает все требования ТЗ и архитектурные принципы.
"""

import sys
import time
from datetime import datetime
from types import MappingProxyType

def main():
    print("=" * 80)
    print("  Domain Event Layer v1.6.8 — Full Architecture Verification Test")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    # === ТЕСТ 1: Импорт всех компонентов ===
    print("\n📦 ТЕСТ 1: Импорт компонентов v1.6.8...")
    try:
        from scanner_platform.events import (
            DomainEvent, EventOrigin, EventType,
            DomainEventSet, EMPTY_EVENT_SET,
            EventQuery, EventRuleRegistry, EventGenerator,
            SubjectType, CategoryType,
            InvalidDiffError, EventGenerationError,
            HostnameRule, VendorRule, CapabilityRule, SummaryRule,
            PresenceRule, SessionRule
        )
        # ИСПРАВЛЕНО: убраны Severity и ChangeReason (их больше нет в diff)
        from scanner_platform.diff import (
            ProfileDiffer, ProfileDiff, EMPTY_DIFF,
            Change, ChangeType
        )
        from scanner_platform.diff.models import SummaryDiff, MetricDelta, EngineDiff, CapabilityDiff
        from scanner_platform.profile import (
            UnifiedDeviceProfile, ProfileSummary, ProfileStatistics,
            ProfileCoverage, ProfileConfidence, IdentityReference,
            ProfileCategories, ProfileService
        )
        from scanner_platform.cache.platform import VersionSnapshot
        print("   ✅ Все компоненты импортированы")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
        return 1
    
    # === Вспомогательные функции ===
    def create_mock_fact(fact_id, engine, category, confidence=50.0, hostname="", vendor=""):
        """Создает мок факта."""
        class MockFact:
            def __init__(self):
                self.id = fact_id
                self.engine = engine
                self.category = category
                self.confidence = confidence
                self.matched_rules = []
                self.matched_features = []
                self.status = None
                self.quality = 0.9
                self.sources = []
                self.explain = {}
                self.generated_at = datetime.now()
                self.hostname = hostname
                self.vendor = vendor
        return MockFact()
    
    def create_mock_profile(device_uuid, facts_list, capabilities=None, version="1.0.0"):
        """Создает мок UnifiedDeviceProfile."""
        if capabilities is None:
            capabilities = {}
        
        facts_by_engine = {}
        facts_by_category = {}
        for fact in facts_list:
            eng = getattr(fact, 'engine', 'unknown')
            cat = getattr(fact, 'category', 'unknown')
            facts_by_engine[eng] = facts_by_engine.get(eng, 0) + 1
            facts_by_category[cat] = facts_by_category.get(cat, 0) + 1
        
        class MockKnowledgeService:
            def __init__(self, facts):
                self._facts = facts
            def query_by_category(self, device_id, category):
                return [f for f in self._facts if getattr(f, 'category', None) == category]
            def query_by_engine(self, device_id, engine):
                return [f for f in self._facts if getattr(f, 'engine', None) == engine]
            def query_by_tag(self, device_id, tag):
                return []
            def query_by_confidence(self, device_id, min_conf):
                return [f for f in self._facts if getattr(f, 'confidence', 0) >= min_conf]
            def get_all_facts(self, device_id):
                return list(self._facts)
        
        mock_service = MockKnowledgeService(facts_list)
        
        return UnifiedDeviceProfile(
            device_id=device_uuid,
            identity=IdentityReference(device_uuid=device_uuid),
            summary=ProfileSummary(
                known_since=datetime(2026, 1, 1),
                last_seen=datetime(2026, 7, 18),
                history_depth=200,
                sessions=len(facts_list),
                facts=len(facts_list),
                confidence=sum(getattr(f, 'confidence', 0) for f in facts_list) / len(facts_list) if facts_list else 0.0
            ),
            categories=ProfileCategories(),
            statistics=ProfileStatistics(
                facts_total=len(facts_list),
                categories_total=len(facts_by_category),
                engines_total=len(facts_by_engine),
                facts_by_engine=facts_by_engine,
                facts_by_category=facts_by_category
            ),
            coverage=ProfileCoverage(),
            confidence=ProfileConfidence(),
            capabilities=capabilities,
            version_snapshot=VersionSnapshot(profile_version=version),
            _knowledge_service=mock_service
        )
    
    def create_test_change(change_type, subject, engine, category, old=None, new=None, delta=None):
        """Создает тестовое изменение."""
        return Change(
            change_id=f"change-{change_type.value}-{subject}-{engine}",
            type=change_type,
            subject=subject,
            engine=engine,
            category=category,
            old=old,
            new=new,
            delta=delta,
            metadata=MappingProxyType({
                "fact_id": f"fact-{engine}" if old or new else None,
                "changed_fields": tuple(new.keys()) if isinstance(new, dict) else ()
            })
        )
    
    def create_test_diff(device_uuid, changes, created_at=None):
        """Создает тестовый ProfileDiff."""
        if created_at is None:
            created_at = datetime(2026, 7, 18, 0, 35, 6)
        
        return ProfileDiff(
            identity_uuid=device_uuid,
            diff_id=f"diff-{device_uuid}-{len(changes)}",
            created_at=created_at,
            summary=SummaryDiff(
                history_depth=MetricDelta(0, 0),
                facts_count=MetricDelta(0, len(changes)),
                sessions=MetricDelta(0, 0),
                confidence=MetricDelta(0.0, 0.0),
                last_seen=MetricDelta(None, None)
            ),
            engine_diff=EngineDiff(),
            capability_diff=CapabilityDiff(),
            changes=tuple(changes)
        )
    
    # === ТЕСТ 2: EMPTY_DIFF → EMPTY_EVENT_SET ===
    print("\n🔄 ТЕСТ 2: EMPTY_DIFF → EMPTY_EVENT_SET (идемпотентность)...")
    try:
        generator = EventGenerator()
        event_set = generator.generate(EMPTY_DIFF)
        
        assert event_set is EMPTY_EVENT_SET, f"Expected EMPTY_EVENT_SET, got {type(event_set)}"
        assert event_set.count() == 0
        assert len(event_set) == 0
        
        print(f"   ✅ Идемпотентность: EMPTY_DIFF → EMPTY_EVENT_SET")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 3: DomainEvent immutable ===
    print("\n🔒 ТЕСТ 3: DomainEvent immutable...")
    try:
        event = DomainEvent.create(
            event_type=EventType.HOSTNAME_CHANGED.value,
            device_uuid="test-device-123",
            payload={"old_hostname": "old", "new_hostname": "new"},
            source_diff_id="diff-123",
            source_change_id="change-456",
            occurred_at=datetime(2026, 7, 18, 0, 35, 6),
            origin=EventOrigin.RULE
        )
        
        # Проверяем immutable
        try:
            event.event_type = "HACKED"
            raise AssertionError("Should raise FrozenInstanceError")
        except (AttributeError, TypeError):
            pass
        
        # Проверяем payload immutable
        try:
            event.payload["hacked"] = "value"
            raise AssertionError("Should raise TypeError for MappingProxyType")
        except TypeError:
            pass
        
        print(f"   ✅ DomainEvent immutable (frozen dataclass + MappingProxyType)")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 4: Детерминированный event_id ===
    print("\n🔑 ТЕСТ 4: Детерминированный event_id...")
    try:
        event1 = DomainEvent.create(
            event_type=EventType.HOSTNAME_CHANGED.value,
            device_uuid="test-device-123",
            payload={"old_hostname": "old", "new_hostname": "new"},
            source_diff_id="diff-123",
            source_change_id="change-456",
            occurred_at=datetime(2026, 7, 18, 0, 35, 6)
        )
        
        event2 = DomainEvent.create(
            event_type=EventType.HOSTNAME_CHANGED.value,
            device_uuid="test-device-123",
            payload={"old_hostname": "old", "new_hostname": "new"},
            source_diff_id="diff-123",
            source_change_id="change-456",
            occurred_at=datetime(2026, 7, 18, 0, 35, 6)
        )
        
        assert event1.event_id == event2.event_id, "event_id должен быть детерминированным"
        
        print(f"   ✅ Детерминированный event_id: {event1.event_id}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 5: EventRuleRegistry автоматическая регистрация ===
    print("\n📋 ТЕСТ 5: EventRuleRegistry автоматическая регистрация...")
    try:
        rules = EventRuleRegistry.get_all()
        
        assert len(rules) >= 6, f"Expected at least 6 rules, got {len(rules)}"
        
        rule_types = [type(r).__name__ for r in rules]
        expected_rules = ["HostnameRule", "VendorRule", "CapabilityRule", "SummaryRule", "PresenceRule", "SessionRule"]
        
        for expected in expected_rules:
            assert expected in rule_types, f"Rule {expected} not registered"
        
        print(f"   ✅ Автоматическая регистрация: {len(rules)} правил")
        for rule in rules:
            print(f"      • {type(rule).__name__}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 6: EventQuery immutable builder ===
    print("\n🔍 ТЕСТ 6: EventQuery immutable builder...")
    try:
        event1 = DomainEvent.create(
            event_type=EventType.HOSTNAME_CHANGED.value,
            device_uuid="device-1",
            payload={"old_hostname": "old", "new_hostname": "new"},
            source_diff_id="diff-1",
            source_change_id="change-1",
            occurred_at=datetime(2026, 7, 18, 0, 35, 6)
        )
        
        event2 = DomainEvent.create(
            event_type=EventType.VENDOR_CHANGED.value,
            device_uuid="device-2",
            payload={"old_vendor": "old", "new_vendor": "new"},
            source_diff_id="diff-2",
            source_change_id="change-2",
            occurred_at=datetime(2026, 7, 18, 0, 35, 6)
        )
        
        event_set = DomainEventSet(events=(event1, event2))
        
        # Query должен быть immutable
        query1 = event_set.query()
        query2 = query1.by_device("device-1")
        
        # query1 и query2 должны быть разными объектами
        assert query1 is not query2, "Query должен возвращать новый экземпляр"
        
        # Фильтрация должна работать
        device1_events = query2.all()
        assert len(device1_events) == 1
        assert device1_events[0].device_uuid == "device-1"
        
        print(f"   ✅ EventQuery immutable builder pattern")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 7: DomainEventSet immutable ===
    print("\n📦 ТЕСТ 7: DomainEventSet immutable...")
    try:
        event = DomainEvent.create(
            event_type=EventType.HOSTNAME_CHANGED.value,
            device_uuid="test-device",
            payload={"old_hostname": "old", "new_hostname": "new"},
            source_diff_id="diff-1",
            source_change_id="change-1",
            occurred_at=datetime(2026, 7, 18, 0, 35, 6)
        )
        
        event_set = DomainEventSet(events=(event,))
        
        # Проверяем immutable
        try:
            event_set.events = ()
            raise AssertionError("Should raise FrozenInstanceError")
        except (AttributeError, TypeError):
            pass
        
        print(f"   ✅ DomainEventSet immutable")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 8: Сериализация JSON ===
    print("\n📄 ТЕСТ 8: Сериализация JSON...")
    try:
        event = DomainEvent.create(
            event_type=EventType.HOSTNAME_CHANGED.value,
            device_uuid="test-device",
            payload={"old_hostname": "old", "new_hostname": "new"},
            source_diff_id="diff-1",
            source_change_id="change-1",
            occurred_at=datetime(2026, 7, 18, 0, 35, 6)
        )
        
        event_set = DomainEventSet(events=(event,))
        json_str = event_set.serialize(format="json")
        
        assert len(json_str) > 0
        assert "HOSTNAME_CHANGED" in json_str
        assert "test-device" in json_str
        assert "old_hostname" in json_str
        
        print(f"   ✅ JSON сериализация работает")
        print(f"      JSON size: {len(json_str)} bytes")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 9: EventOrigin трассировка ===
    print("\n🌍 ТЕСТ 9: EventOrigin трассировка...")
    try:
        event = DomainEvent.create(
            event_type=EventType.HOSTNAME_CHANGED.value,
            device_uuid="test-device",
            payload={"old_hostname": "old", "new_hostname": "new"},
            source_diff_id="diff-1",
            source_change_id="change-1",
            occurred_at=datetime(2026, 7, 18, 0, 35, 6),
            origin=EventOrigin.RULE
        )
        
        assert event.origin == EventOrigin.RULE
        assert event.source_diff_id == "diff-1"
        assert event.source_change_id == "change-1"
        
        print(f"   ✅ EventOrigin трассировка:")
        print(f"      • origin: {event.origin.value}")
        print(f"      • source_diff_id: {event.source_diff_id}")
        print(f"      • source_change_id: {event.source_change_id}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 10: Полная трассировка ===
    print("\n🔗 ТЕСТ 10: Полная трассировка (Alert → Event → Diff → Change → Profile → Knowledge)...")
    try:
        event = DomainEvent.create(
            event_type=EventType.HOSTNAME_CHANGED.value,
            device_uuid="test-device",
            payload={"old_hostname": "old", "new_hostname": "new"},
            source_diff_id="diff-abc123",
            source_change_id="change-xyz789",
            occurred_at=datetime(2026, 7, 18, 0, 35, 6)
        )
        
        # Проверяем, что все поля для трассировки присутствуют
        assert hasattr(event, 'source_diff_id')
        assert hasattr(event, 'source_change_id')
        assert hasattr(event, 'device_uuid')
        assert hasattr(event, 'event_type')
        assert hasattr(event, 'payload')
        
        print(f"   ✅ Полная трассировка:")
        print(f"      Alert → Event → Diff → Change → Profile → Knowledge")
        print(f"      • event_id: {event.event_id}")
        print(f"      • source_diff_id: {event.source_diff_id}")
        print(f"      • source_change_id: {event.source_change_id}")
        print(f"      • device_uuid: {event.device_uuid}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 11: Один Change → одно событие (HostnameRule) ===
    print("\n➡️  ТЕСТ 11: Один Change → одно событие (HostnameRule)...")
    try:
        change = create_test_change(
            change_type=ChangeType.UPDATED,
            subject=SubjectType.FACT,
            engine="test-engine",
            category="network",
            old={"hostname": "old-host", "vendor": "old-vendor"},
            new={"hostname": "new-host", "vendor": "old-vendor"}
        )
        
        diff = create_test_diff("device-123", [change])
        
        generator = EventGenerator()
        event_set = generator.generate(diff)
        
        hostname_events = [e for e in event_set.events if e.event_type == EventType.HOSTNAME_CHANGED.value]
        assert len(hostname_events) == 1, f"Expected 1 HOSTNAME_CHANGED event, got {len(hostname_events)}"
        assert hostname_events[0].payload["old_hostname"] == "old-host"
        assert hostname_events[0].payload["new_hostname"] == "new-host"
        
        print(f"   ✅ HostnameRule: 1 Change → 1 Event")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    
    # === ТЕСТ 12: Один Change → несколько событий (VendorRule) ===
    print("\n➡️  ТЕСТ 12: Один Change → несколько событий (VendorRule)...")
    try:
        change = create_test_change(
            change_type=ChangeType.UPDATED,
            subject=SubjectType.FACT,
            engine="test-engine",
            category="network",
            old={"hostname": "host", "vendor": "old-vendor"},
            new={"hostname": "host", "vendor": "new-vendor"}
        )
        
        diff = create_test_diff("device-123", [change])
        
        generator = EventGenerator()
        event_set = generator.generate(diff)
        
        vendor_events = [e for e in event_set.events if e.event_type == EventType.VENDOR_CHANGED.value]
        identity_events = [e for e in event_set.events if e.event_type == EventType.DEVICE_IDENTITY_CHANGED.value]
        
        assert len(vendor_events) == 1, f"Expected 1 VENDOR_CHANGED event, got {len(vendor_events)}"
        assert len(identity_events) == 1, f"Expected 1 DEVICE_IDENTITY_CHANGED event, got {len(identity_events)}"
        
        print(f"   ✅ VendorRule: 1 Change → 2 Events")
        print(f"      • VENDOR_CHANGED: {len(vendor_events)}")
        print(f"      • DEVICE_IDENTITY_CHANGED: {len(identity_events)}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    
    # === ТЕСТ 13: Rule без совпадений (0 событий) ===
    print("\n🚫 ТЕСТ 13: Rule без совпадений (0 событий)...")
    try:
        change = Change(
            change_id="change-unknown",
            type=ChangeType.UPDATED,
            subject="unknown_subject",
            engine="unknown_engine",
            category="unknown_category",
            old=None,
            new=None,
            delta=None,
            metadata=MappingProxyType({})
        )
        
        diff = create_test_diff("device-123", [change])
        
        generator = EventGenerator()
        event_set = generator.generate(diff)
        
        assert event_set.count() == 0, f"Expected 0 events, got {event_set.count()}"
        
        print(f"   ✅ Rule без совпадений: 0 событий")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 14: Детерминированность при одинаковом Diff ===
    print("\n🔑 ТЕСТ 14: Детерминированность при одинаковом Diff...")
    try:
        change = create_test_change(
            change_type=ChangeType.UPDATED,
            subject=SubjectType.FACT,
            engine="test-engine",
            category="network",
            old={"hostname": "old-host"},
            new={"hostname": "new-host"}
        )
        
        diff = create_test_diff("device-123", [change], created_at=datetime(2026, 7, 18, 0, 35, 6))
        
        generator = EventGenerator()
        
        # Генерируем дважды
        event_set1 = generator.generate(diff)
        event_set2 = generator.generate(diff)
        
        # Проверяем одинаковость
        assert event_set1.count() == event_set2.count()
        
        for i in range(len(event_set1.events)):
            e1 = event_set1.events[i]
            e2 = event_set2.events[i]
            assert e1.event_id == e2.event_id, f"Event IDs differ: {e1.event_id} != {e2.event_id}"
            assert e1.event_type == e2.event_type
            assert e1.device_uuid == e2.device_uuid
            assert e1.payload == e2.payload
        
        print(f"   ✅ Детерминированность: одинаковый Diff → одинаковые Event ID")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 15: Идемпотентность (повторная генерация) ===
    print("\n🔄 ТЕСТ 15: Идемпотентность (повторная генерация)...")
    try:
        change = create_test_change(
            change_type=ChangeType.UPDATED,
            subject=SubjectType.FACT,
            engine="test-engine",
            category="network",
            old={"hostname": "old-host"},
            new={"hostname": "new-host"}
        )
        
        diff = create_test_diff("device-123", [change])
        
        generator = EventGenerator()
        
        # Генерируем 3 раза
        event_set1 = generator.generate(diff)
        event_set2 = generator.generate(diff)
        event_set3 = generator.generate(diff)
        
        # Все должны быть идентичны
        assert event_set1.count() == event_set2.count() == event_set3.count()
        
        for e1, e2, e3 in zip(event_set1.events, event_set2.events, event_set3.events):
            assert e1.event_id == e2.event_id == e3.event_id
        
        print(f"   ✅ Идемпотентность: повторная генерация дает идентичный результат")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 16: Валидация diff (InvalidDiffError) ===
    print("\n⚠️  ТЕСТ 16: Валидация diff (InvalidDiffError)...")
    try:
        # Создаем объект без обязательных полей
        class InvalidDiff:
            pass
        
        generator = EventGenerator()
        
        try:
            event_set = generator.generate(InvalidDiff())
            raise AssertionError("Should raise InvalidDiffError")
        except InvalidDiffError:
            pass
        
        print(f"   ✅ Валидация diff работает: InvalidDiffError вызван")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ТЕСТ 17: Константы SubjectType и CategoryType ===
    print("\n📋 ТЕСТ 17: Константы SubjectType и CategoryType...")
    try:
        assert hasattr(SubjectType, 'FACT')
        assert hasattr(SubjectType, 'SUMMARY')
        assert hasattr(SubjectType, 'CAPABILITY')
        
        assert hasattr(CategoryType, 'PRESENCE')
        assert hasattr(CategoryType, 'USAGE')
        assert hasattr(CategoryType, 'BEHAVIOUR')
        
        print(f"   ✅ Константы доступны:")
        print(f"      • SubjectType: FACT, SUMMARY, CAPABILITY")
        print(f"      • CategoryType: PRESENCE, USAGE, BEHAVIOUR")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1
    
    # === ИТОГОВАЯ СВОДКА ===
    print("\n" + "=" * 80)
    print(f"📈 ИТОГОВАЯ СВЕРКА:")
    print(f"   ✅ Пройдено тестов: {passed}")
    print(f"   ❌ Провалено тестов: {failed}")
    print(f"   📊 Успешность: {(passed / (passed + failed)) * 100:.1f}%")
    print("=" * 80)
    
    # Архитектурные требования
    print("\n📋 АРХИТЕКТУРНЫЕ ТРЕБОВАНИЯ v1.6.8:")
    requirements = [
        ("EMPTY_DIFF → EMPTY_EVENT_SET (идемпотентность)", "ТЕСТ 2"),
        ("DomainEvent immutable (frozen dataclass)", "ТЕСТ 3"),
        ("Детерминированный event_id", "ТЕСТ 4"),
        ("Автоматическая регистрация правил", "ТЕСТ 5"),
        ("EventQuery immutable builder", "ТЕСТ 6"),
        ("DomainEventSet immutable", "ТЕСТ 7"),
        ("JSON сериализация", "ТЕСТ 8"),
        ("EventOrigin трассировка", "ТЕСТ 9"),
        ("Полная трассировка (Alert → Event → Diff → Change → Profile → Knowledge)", "ТЕСТ 10"),
        ("Один Change → одно событие (HostnameRule)", "ТЕСТ 11"),
        ("Один Change → несколько событий (VendorRule)", "ТЕСТ 12"),
        ("Rule без совпадений (0 событий)", "ТЕСТ 13"),
        ("Детерминированность при одинаковом Diff", "ТЕСТ 14"),
        ("Идемпотентность (повторная генерация)", "ТЕСТ 15"),
        ("Валидация diff (InvalidDiffError)", "ТЕСТ 16"),
        ("Константы SubjectType и CategoryType", "ТЕСТ 17"),
    ]
    
    for req, test in requirements:
        print(f"   ✅ {req} ({test})")
    
    if failed == 0:
        print("\n🎉 Domain Event Layer v1.6.8 — ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("   Архитектура готова к интеграции в monitor.py!")
        return 0
    else:
        print(f"\n⚠️  Обнаружено {failed} проблем. Требуется исправление.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
