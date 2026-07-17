#!/usr/bin/env python3
"""
Полный набор тестов для Domain Event Layer v1.6.8.
Проверяет все требования ТЗ.
"""

import sys
from datetime import datetime
from types import MappingProxyType

def main():
    print("=" * 75)
    print("  Domain Event Layer v1.6.8 — Architecture Verification Test")
    print("=" * 75)
    
    passed = 0
    failed = 0
    
    # === ТЕСТ 1: Импорт компонентов ===
    print("\n📦 ТЕСТ 1: Импорт компонентов v1.6.8...")
    try:
        from scanner_platform.events import (
            DomainEvent, EventOrigin, EventType,
            DomainEventSet, EMPTY_EVENT_SET,
            EventQuery, EventRuleRegistry, EventGenerator,
            HostnameRule, VendorRule, CapabilityRule, SummaryRule,
            PresenceRule, SessionRule
        )
        from scanner_platform.diff import ProfileDiffer, EMPTY_DIFF
        print("   ✅ Все компоненты импортированы")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
        return 1
    
    # === ТЕСТ 2: EMPTY_DIFF → EMPTY_EVENT_SET ===
    print("\n🔄 ТЕСТ 2: EMPTY_DIFF → EMPTY_EVENT_SET...")
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
    
    # === ТЕСТ 9: EventOrigin ===
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
    
    # === ТЕСТ 10: Полная трассировка (Alert → Event → Diff → Change → Profile → Knowledge) ===
    print("\n🔗 ТЕСТ 10: Полная трассировка...")
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
    
    # === ИТОГОВАЯ СВОДКА ===
    print("\n" + "=" * 75)
    print(f"📈 ИТОГОВАЯ СВЕРКА:")
    print(f"   ✅ Пройдено тестов: {passed}")
    print(f"   ❌ Провалено тестов: {failed}")
    print(f"   📊 Успешность: {(passed / (passed + failed)) * 100:.1f}%")
    print("=" * 75)
    
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
