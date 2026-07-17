#!/usr/bin/env python3
"""Полная проверка Domain Event Layer v1.6.8 по ТЗ"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner_platform.diff.models import ProfileDiff, Change, ChangeType, EMPTY_DIFF
from scanner_platform.events import (
    EventGenerator,
    DomainEventSet,
    EMPTY_EVENT_SET,
    EventType,
    EventOrigin,
    SubjectType,
    CategoryType,
    InvalidDiffError,
    EventGenerationError,
    EventQuery,
    DomainEvent
)


def print_header():
    print("=" * 80)
    print("🔍 ПОЛНАЯ ПРОВЕРКА DOMAIN EVENT LAYER v1.6.8")
    print("=" * 80)


def test_01_imports():
    """1. Все компоненты успешно импортируются"""
    print("\n[01] Проверка импортов...")
    required = [
        "EventGenerator", "DomainEventSet", "EMPTY_EVENT_SET", "DomainEvent",
        "EventType", "EventOrigin", "SubjectType", "CategoryType",
        "InvalidDiffError", "EventGenerationError", "EventQuery"
    ]
    for name in required:
        assert name in globals(), f"Не импортирован: {name}"
    print("✅ Все компоненты импортированы")


def test_02_empty_diff():
    """2. EMPTY_DIFF → EMPTY_EVENT_SET"""
    print("\n[02] Проверка EMPTY_DIFF...")
    generator = EventGenerator()
    result = generator.generate(EMPTY_DIFF)
    
    assert result is EMPTY_EVENT_SET
    assert len(result) == 0
    assert result.count() == 0
    print("✅ EMPTY_DIFF обработан корректно")


def create_test_diff() -> ProfileDiff:
    """Создаёт богатый тестовый diff"""
    changes = [
        # Hostname change
        Change(change_id="c1", subject=SubjectType.FACT, type=ChangeType.UPDATED,
                old={"hostname": "old-pc"}, new={"hostname": "new-pc"},
                metadata={"changed_fields": ["hostname"]}, engine="behaviour", category=None, delta=None),
        
        # Capability added
        Change(change_id="c2", subject=SubjectType.CAPABILITY, type=ChangeType.ADDED,
                old=None, new="wifi_repeater_detection",
                metadata={}, engine="repeater", category=None, delta=None),
        
        # Summary / Sessions
        Change(change_id="c3", subject=SubjectType.SUMMARY, type=ChangeType.UPDATED,
                old=5, new=8, delta=3, metadata={},
                engine="session", category=CategoryType.SESSIONS),
        
        # Presence appeared
        Change(change_id="c4", subject=SubjectType.FACT, type=ChangeType.ADDED,
                old=None, new="online", metadata={"fact_id": "f-pres1"},
                engine="presence", category=CategoryType.PRESENCE, delta=None),
    ]
    
    return ProfileDiff(
        diff_id="diff_full_test_001",
        identity_uuid="device-uuid-abc123",
        created_at=datetime(2026, 7, 18, 12, 0, 0),
        changes=changes
    )


def test_03_generation():
    """3. Генерация событий (1 Change → 0..N Events)"""
    print("\n[03] Проверка генерации событий...")
    generator = EventGenerator()
    diff = create_test_diff()
    event_set = generator.generate(diff)
    
    assert len(event_set) >= 5, f"Ожидалось >=5 событий, получено {len(event_set)}"
    
    types = {e.event_type for e in event_set}
    assert EventType.HOSTNAME_CHANGED.value in types
    assert EventType.CAPABILITY_ADDED.value in types
    assert EventType.SESSION_STARTED.value in types
    assert EventType.PRESENCE_APPEARED.value in types
    
    print(f"✅ Сгенерировано {len(event_set)} событий")


def test_04_determinism():
    """4. Детерминированность + Идемпотентность"""
    print("\n[04] Проверка детерминированности...")
    generator = EventGenerator()
    diff = create_test_diff()
    
    set1 = generator.generate(diff)
    set2 = generator.generate(diff)
    
    assert set1.events == set2.events
    assert set1.generated_at == set2.generated_at
    
    # Проверка event_id
    ids = [e.event_id for e in set1]
    assert len(set(ids)) == len(ids), "Event ID должны быть уникальными в рамках одного набора"
    
    print("✅ Детерминированность и идемпотентность подтверждены")


def test_05_immutable():
    """5. Полная неизменяемость"""
    print("\n[05] Проверка Immutable...")
    event_set = EventGenerator().generate(create_test_diff())
    event = event_set.first()
    
    for attr in ['event_id', 'event_type', 'device_uuid']:
        try:
            setattr(event, attr, "hacked")
            assert False, f"Поле {attr} удалось изменить!"
        except (AttributeError, TypeError):
            pass
    
    try:
        event.payload['new_key'] = 42
        assert False
    except TypeError:
        pass
    
    print("✅ Все объекты immutable")


def test_06_query_api():
    """6. Fluent Query API"""
    print("\n[06] Проверка Query API...")
    event_set = EventGenerator().generate(create_test_diff())
    q = event_set.query()
    
    assert q.by_type(EventType.HOSTNAME_CHANGED.value).count() >= 1
    assert q.by_device("device-uuid-abc123").count() == len(event_set)
    assert q.by_diff("diff_full_test_001").count() == len(event_set)
    
    # Цепочка
    filtered = q.by_type(EventType.CAPABILITY_ADDED.value).by_change("c2").all()
    assert len(filtered) >= 1
    
    print("✅ Query API работает корректно")


def test_07_serialization():
    """7. Сериализация"""
    print("\n[07] Проверка сериализации...")
    event_set = EventGenerator().generate(create_test_diff())
    json_data = event_set.serialize("json")
    
    parsed = json.loads(json_data)
    assert "events" in parsed
    assert "generated_at" in parsed
    assert parsed["count"] == len(event_set)
    
    print("✅ Сериализация работает")


def test_08_error_handling():
    """8. Обработка ошибок"""
    print("\n[08] Проверка обработки ошибок...")
    generator = EventGenerator()
    
    try:
        generator.generate(None)
        assert False
    except (InvalidDiffError, EventGenerationError):
        pass
    
    print("✅ Обработка ошибок работает")


def test_09_origin_and_trace():
    """9. Трассировка происхождения"""
    print("\n[09] Проверка трассировки...")
    event_set = EventGenerator().generate(create_test_diff())
    
    for event in event_set:
        assert event.origin == EventOrigin.RULE
        assert event.source_diff_id is not None
        assert event.source_change_id is not None
        assert event.device_uuid is not None
    
    print("✅ Трассировка (origin + source_*) присутствует")


def main():
    print_header()
    
    try:
        test_01_imports()
        test_02_empty_diff()
        test_03_generation()
        test_04_determinism()
        test_05_immutable()
        test_06_query_api()
        test_07_serialization()
        test_08_error_handling()
        test_09_origin_and_trace()
        
        print("\n" + "="*80)
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("Domain Event Layer v1.6.8 соответствует ТЗ.")
        print("="*80)
        return 0
        
    except Exception as e:
        print(f"\n❌ ТЕСТ УПАЛ: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
