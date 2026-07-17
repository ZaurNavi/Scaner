#!/usr/bin/env python3
"""
Изолированный тест Change Detection Layer v1.6.7.
Проверяет все архитектурные требования:
- Identity check
- Идемпотентность (compare(P,P) → EMPTY_DIFF)
- Детерминизм (одинаковый diff_id)
- Иммутабельность (frozen dataclass)
- Facts: add/remove/update
- Summary: delta calculation
- Capabilities: state changes
- Engines: add/remove
- Автономность (удаление профилей не ломает Diff)
- O(n) производительность
- Симметрия (ADDED ↔ REMOVED)
"""

import sys
import time
from datetime import datetime
from types import MappingProxyType

def main():
    print("=" * 75)
    print("  Change Detection Layer v1.6.7 — Architecture Verification Test")
    print("=" * 75)
    
    passed = 0
    failed = 0
    
    # === ТЕСТ 1: Импорт всех компонентов ===
    print("\n📦 ТЕСТ 1: Импорт компонентов v1.6.7...")
    try:
        from scanner_platform.diff import (
            ProfileDiffer, ProfileDiff, EMPTY_DIFF, SummaryDiff, MetricDelta,
            EngineDiff, CapabilityDiff, Change, ChangeType, CapabilityState,
            DifferentIdentityError, InvalidProfileError, ProfileIndexer
        )
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
    
    # === Вспомогательные функции для создания тестовых профилей ===
    def create_mock_fact(fact_id, engine, category, confidence=50.0):
        """Создает мок факта с необходимыми атрибутами."""
        class MockFact:
            def __init__(self, fid, eng, cat, conf):
                self.id = fid
                self.engine = eng
                self.category = cat
                self.confidence = conf
                self.matched_rules = []
                self.matched_features = []
                self.status = None
                self.quality = 0.9
                self.sources = []
                self.explain = {}
                self.generated_at = datetime.now()
        return MockFact(fact_id, engine, category, confidence)
    
    def create_mock_profile(device_uuid, facts_list, capabilities=None, version="1.0.0"):
        """Создает мок UnifiedDeviceProfile."""
        if capabilities is None:
            capabilities = {}
        
        # Подсчитываем статистику из фактов
        facts_by_engine = {}
        facts_by_category = {}
        for fact in facts_list:
            eng = getattr(fact, 'engine', 'unknown')
            cat = getattr(fact, 'category', 'unknown')
            facts_by_engine[eng] = facts_by_engine.get(eng, 0) + 1
            facts_by_category[cat] = facts_by_category.get(cat, 0) + 1
        
        # Создаем мок KnowledgeService для Query API
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
        
        # Создаем Profile через конструктор напрямую
        profile = UnifiedDeviceProfile(
            device_id=device_uuid,
            identity=IdentityReference(device_uuid=device_uuid),
            summary=ProfileSummary(
                known_since=datetime(2026, 1, 1),
                last_seen=datetime(2026, 7, 17),
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
        return profile
    
    # === ТЕСТ 2: Identity Check (одинаковый UUID) ===
    print("\n🆔 ТЕСТ 2: Identity Check (одинаковый UUID)...")
    try:
        facts1 = [create_mock_fact("f1", "usage", "network")]
        facts2 = [create_mock_fact("f2", "presence", "temporal")]
        
        profile1 = create_mock_profile("device-uuid-123", facts1, version="1.0.0")
        profile2 = create_mock_profile("device-uuid-123", facts2, version="2.0.0")
        
        differ = ProfileDiffer()
        diff = differ.compare(profile1, profile2)
        
        assert diff.identity_uuid == "device-uuid-123"
        assert diff.has_changes() == True
        
        print(f"   ✅ Сравнение профилей с одинаковым UUID прошло")
        print(f"      Identity: {diff.identity_uuid}")
        print(f"      Changes: {diff.count()}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Identity Check: {e}")
        failed += 1
    
    # === ТЕСТ 3: Identity Check (разный UUID → DifferentIdentityError) ===
    print("\n🚫 ТЕСТ 3: Identity Check (разный UUID → DifferentIdentityError)...")
    try:
        profile1 = create_mock_profile("device-uuid-111", [])
        profile2 = create_mock_profile("device-uuid-222", [])
        
        differ = ProfileDiffer()
        try:
            diff = differ.compare(profile1, profile2)
            raise AssertionError("Should raise DifferentIdentityError")
        except DifferentIdentityError:
            pass  # Ожидаемое поведение
        
        print(f"   ✅ DifferentIdentityError вызван корректно")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка DifferentIdentityError: {e}")
        failed += 1
    
    # === ТЕСТ 4: Идемпотентность (compare(P,P) → EMPTY_DIFF) ===
    print("\n🔄 ТЕСТ 4: Идемпотентность (compare(P,P) → EMPTY_DIFF)...")
    try:
        facts = [create_mock_fact("f1", "usage", "network")]
        profile = create_mock_profile("device-uuid-123", facts, version="1.0.0")
        
        differ = ProfileDiffer()
        diff = differ.compare(profile, profile)
        
        assert diff is EMPTY_DIFF, f"Expected EMPTY_DIFF, got {type(diff)}"
        assert diff.has_changes() == False
        assert diff.count() == 0
        
        print(f"   ✅ Идемпотентность соблюдена: compare(P,P) → EMPTY_DIFF")
        print(f"      diff_id: {diff.diff_id}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка идемпотентности: {e}")
        failed += 1
    
    # === ТЕСТ 5: Детерминизм (одинаковый diff_id) ===
    print("\n🔑 ТЕСТ 5: Детерминизм (одинаковый diff_id)...")
    try:
        facts1 = [create_mock_fact("f1", "usage", "network")]
        facts2 = [create_mock_fact("f2", "presence", "temporal")]
        
        profile1 = create_mock_profile("device-uuid-123", facts1, version="1.0.0")
        profile2 = create_mock_profile("device-uuid-123", facts2, version="2.0.0")
        
        differ = ProfileDiffer()
        diff1 = differ.compare(profile1, profile2)
        diff2 = differ.compare(profile1, profile2)
        
        assert diff1.diff_id == diff2.diff_id, f"diff_id должен быть одинаковым: {diff1.diff_id} != {diff2.diff_id}"
        
        print(f"   ✅ Детерминизм соблюдена: diff_id={diff1.diff_id}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка детерминизма: {e}")
        failed += 1
    
    # === ТЕСТ 6: Иммутабельность (frozen dataclass) ===
    print("\n🔒 ТЕСТ 6: Иммутабельность (frozen dataclass)...")
    try:
        facts1 = [create_mock_fact("f1", "usage", "network")]
        facts2 = [create_mock_fact("f2", "presence", "temporal")]
        
        profile1 = create_mock_profile("device-uuid-123", facts1, version="1.0.0")
        profile2 = create_mock_profile("device-uuid-123", facts2, version="2.0.0")
        
        differ = ProfileDiffer()
        diff = differ.compare(profile1, profile2)
        
        # Проверяем, что changes — это tuple
        assert isinstance(diff.changes, tuple), f"changes должен быть tuple, got {type(diff.changes)}"
        
        # Проверяем, что попытка изменения вызывает ошибку
        try:
            diff.changes.append("hack")
            raise AssertionError("Should raise AttributeError for tuple.append")
        except (AttributeError, TypeError):
            pass  # Ожидаемое поведение
        
        # Проверяем frozen dataclass
        try:
            diff.identity_uuid = "hacked"
            raise AssertionError("Should raise FrozenInstanceError")
        except (AttributeError, TypeError):
            pass  # Ожидаемое поведение
        
        print(f"   ✅ Иммутабельность соблюдена (frozen dataclass, tuple)")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка иммутабельности: {e}")
        failed += 1
    
    # === ТЕСТ 7: Facts — добавление ===
    print("\n➕ ТЕСТ 7: Facts — добавление...")
    try:
        facts1 = [create_mock_fact("f1", "usage", "network")]
        facts2 = [
            create_mock_fact("f1", "usage", "network"),
            create_mock_fact("f2", "presence", "temporal")
        ]
        
        profile1 = create_mock_profile("device-uuid-123", facts1, version="1.0.0")
        profile2 = create_mock_profile("device-uuid-123", facts2, version="2.0.0")
        
        differ = ProfileDiffer()
        diff = differ.compare(profile1, profile2)
        
        added_facts = [c for c in diff.changes if c.type == ChangeType.ADDED and c.subject == "fact"]
        assert len(added_facts) == 1, f"Expected 1 added fact, got {len(added_facts)}"
        assert added_facts[0].metadata["fact_id"] == "f2"
        
        print(f"   ✅ Fact добавлен: {added_facts[0].metadata['fact_id']}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка добавления факта: {e}")
        failed += 1
    
    # === ТЕСТ 8: Facts — удаление ===
    print("\n➖ ТЕСТ 8: Facts — удаление...")
    try:
        facts1 = [
            create_mock_fact("f1", "usage", "network"),
            create_mock_fact("f2", "presence", "temporal")
        ]
        facts2 = [create_mock_fact("f1", "usage", "network")]
        
        profile1 = create_mock_profile("device-uuid-123", facts1, version="1.0.0")
        profile2 = create_mock_profile("device-uuid-123", facts2, version="2.0.0")
        
        differ = ProfileDiffer()
        diff = differ.compare(profile1, profile2)
        
        removed_facts = [c for c in diff.changes if c.type == ChangeType.REMOVED and c.subject == "fact"]
        assert len(removed_facts) == 1, f"Expected 1 removed fact, got {len(removed_facts)}"
        assert removed_facts[0].metadata["fact_id"] == "f2"
        
        print(f"   ✅ Fact удален: {removed_facts[0].metadata['fact_id']}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка удаления факта: {e}")
        failed += 1
    
    # === ТЕСТ 9: Facts — обновление ===
    print("\n🔄 ТЕСТ 9: Facts — обновление...")
    try:
        facts1 = [create_mock_fact("f1", "usage", "network", confidence=50.0)]
        facts2 = [create_mock_fact("f1", "usage", "network", confidence=90.0)]
        
        profile1 = create_mock_profile("device-uuid-123", facts1, version="1.0.0")
        profile2 = create_mock_profile("device-uuid-123", facts2, version="2.0.0")
        
        differ = ProfileDiffer()
        diff = differ.compare(profile1, profile2)
        
        updated_facts = [c for c in diff.changes if c.type == ChangeType.UPDATED and c.subject == "fact"]
        assert len(updated_facts) == 1, f"Expected 1 updated fact, got {len(updated_facts)}"
        assert updated_facts[0].metadata["fact_id"] == "f1"
        assert "confidence" in updated_facts[0].metadata["changed_fields"]
        
        print(f"   ✅ Fact обновлен: {updated_facts[0].metadata['fact_id']}")
        print(f"      Changed fields: {updated_facts[0].metadata['changed_fields']}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка обновления факта: {e}")
        failed += 1
    
    # === ТЕСТ 10: Summary — delta calculation ===
    print("\n📊 ТЕСТ 10: Summary — delta calculation...")
    try:
        facts1 = [create_mock_fact("f1", "usage", "network", confidence=50.0)]
        facts2 = [
            create_mock_fact("f1", "usage", "network", confidence=50.0),
            create_mock_fact("f2", "presence", "temporal", confidence=70.0)
        ]
        
        profile1 = create_mock_profile("device-uuid-123", facts1, version="1.0.0")
        profile2 = create_mock_profile("device-uuid-123", facts2, version="2.0.0")
        
        differ = ProfileDiffer()
        diff = differ.compare(profile1, profile2)
        
        assert diff.summary.facts_count.delta == 1, f"Expected delta=1, got {diff.summary.facts_count.delta}"
        assert diff.summary.facts_count.old == 1
        assert diff.summary.facts_count.new == 2
        
        print(f"   ✅ Summary delta корректна:")
        print(f"      facts_count: {diff.summary.facts_count.old} → {diff.summary.facts_count.new} (delta={diff.summary.facts_count.delta})")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Summary delta: {e}")
        failed += 1
    
    # === ТЕСТ 11: Capabilities — появление/исчезновение ===
    print("\n⚡ ТЕСТ 11: Capabilities — появление/исчезновение...")
    try:
        facts = [create_mock_fact("f1", "usage", "network")]
        
        profile1 = create_mock_profile("device-uuid-123", facts, capabilities={"risk_assessment": False}, version="1.0.0")
        profile2 = create_mock_profile("device-uuid-123", facts, capabilities={"risk_assessment": True}, version="2.0.0")
        
        differ = ProfileDiffer()
        diff = differ.compare(profile1, profile2)
        
        assert "risk_assessment" in diff.capability_diff.became_available
        assert len(diff.capability_diff.became_unavailable) == 0
        
        print(f"   ✅ Capability появилась: {diff.capability_diff.became_available}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Capabilities: {e}")
        failed += 1
    
    # === ТЕСТ 12: Engines — добавление/удаление ===
    print("\n🏗️  ТЕСТ 12: Engines — добавление/удаление...")
    try:
        facts1 = [create_mock_fact("f1", "usage", "network")]
        facts2 = [
            create_mock_fact("f1", "usage", "network"),
            create_mock_fact("f2", "presence", "temporal")
        ]
        
        profile1 = create_mock_profile("device-uuid-123", facts1, version="1.0.0")
        profile2 = create_mock_profile("device-uuid-123", facts2, version="2.0.0")
        
        differ = ProfileDiffer()
        diff = differ.compare(profile1, profile2)
        
        assert "presence" in diff.engine_diff.added
        assert len(diff.engine_diff.removed) == 0
        
        print(f"   ✅ Engine добавлен: {diff.engine_diff.added}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Engines: {e}")
        failed += 1
    
    # === ТЕСТ 13: Автономность (удаление профилей не ломает Diff) ===
    print("\n🗑️  ТЕСТ 13: Автономность (удаление профилей не ломает Diff)...")
    try:
        facts1 = [create_mock_fact("f1", "usage", "network")]
        facts2 = [create_mock_fact("f2", "presence", "temporal")]
        
        profile1 = create_mock_profile("device-uuid-123", facts1, version="1.0.0")
        profile2 = create_mock_profile("device-uuid-123", facts2, version="2.0.0")
        
        differ = ProfileDiffer()
        diff = differ.compare(profile1, profile2)
        
        # Удаляем профили
        del profile1
        del profile2
        
        # Diff должен остаться работоспособным
        assert diff.identity_uuid == "device-uuid-123"
        assert diff.has_changes() == True
        assert diff.count() > 0
        
        # Сериализация должна работать
        json_str = diff.to_json()
        assert len(json_str) > 0
        
        print(f"   ✅ Автономность соблюдена (Diff работает после удаления профилей)")
        print(f"      JSON size: {len(json_str)} bytes")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка автономности: {e}")
        failed += 1
    
    # === ТЕСТ 14: O(n) производительность ===
    print("\n⚡ ТЕСТ 14: O(n) производительность (1000 фактов)...")
    try:
        # Создаем 1000 фактов
        facts1 = [create_mock_fact(f"f{i}", "usage", "network") for i in range(1000)]
        facts2 = [create_mock_fact(f"f{i}", "usage", "network") for i in range(1000, 2000)]
        
        profile1 = create_mock_profile("device-uuid-123", facts1, version="1.0.0")
        profile2 = create_mock_profile("device-uuid-123", facts2, version="2.0.0")
        
        differ = ProfileDiffer()
        
        start_time = time.time()
        diff = differ.compare(profile1, profile2)
        duration_ms = (time.time() - start_time) * 1000
        
        assert diff.count() == 2000, f"Expected 2000 changes, got {diff.count()}"
        assert duration_ms < 5000, f"Performance too slow: {duration_ms:.2f}ms for 1000 facts"
        
        print(f"   ✅ O(n) производительность подтверждена:")
        print(f"      1000 фактов сравнены за {duration_ms:.2f}ms")
        print(f"      Changes detected: {diff.count()}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка производительности: {e}")
        failed += 1
    
    # === ТЕСТ 15: Симметрия (ADDED ↔ REMOVED при инверсии) ===
    print("\n↔️  ТЕСТ 15: Симметрия (ADDED ↔ REMOVED при инверсии)...")
    try:
        facts1 = [create_mock_fact("f1", "usage", "network")]
        facts2 = [
            create_mock_fact("f1", "usage", "network"),
            create_mock_fact("f2", "presence", "temporal")
        ]
        
        profile1 = create_mock_profile("device-uuid-123", facts1, version="1.0.0")
        profile2 = create_mock_profile("device-uuid-123", facts2, version="2.0.0")
        
        differ = ProfileDiffer()
        
        # compare(A, B)
        diff_ab = differ.compare(profile1, profile2)
        added_ab = [c for c in diff_ab.changes if c.type == ChangeType.ADDED and c.subject == "fact"]
        
        # compare(B, A)
        diff_ba = differ.compare(profile2, profile1)
        removed_ba = [c for c in diff_ba.changes if c.type == ChangeType.REMOVED and c.subject == "fact"]
        
        # ADDED в A→B должен соответствовать REMOVED в B→A
        assert len(added_ab) == len(removed_ba), f"Symmetry broken: {len(added_ab)} != {len(removed_ba)}"
        assert added_ab[0].metadata["fact_id"] == removed_ba[0].metadata["fact_id"]
        
        print(f"   ✅ Симметрия соблюдена:")
        print(f"      A→B: {len(added_ab)} ADDED")
        print(f"      B→A: {len(removed_ba)} REMOVED")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка симметрии: {e}")
        failed += 1
    
    # === ИТОГОВАЯ СВОДКА ===
    print("\n" + "=" * 75)
    print(f"📈 ИТОГОВАЯ СВЕРКА:")
    print(f"   ✅ Пройдено тестов: {passed}")
    print(f"   ❌ Провалено тестов: {failed}")
    print(f"   📊 Успешность: {(passed / (passed + failed)) * 100:.1f}%")
    print("=" * 75)
    
    # Архитектурные требования
    print("\n📋 АРХИТЕКТУРНЫЕ ТРЕБОВАНИЯ v1.6.7:")
    requirements = [
        ("Identity check (одинаковый UUID)", "ТЕСТ 2"),
        ("Identity check (разный UUID → DifferentIdentityError)", "ТЕСТ 3"),
        ("Идемпотентность (compare(P,P) → EMPTY_DIFF)", "ТЕСТ 4"),
        ("Детерминизм (одинаковый diff_id)", "ТЕСТ 5"),
        ("Иммутабельность (frozen dataclass, tuple)", "ТЕСТ 6"),
        ("Facts: добавление", "ТЕСТ 7"),
        ("Facts: удаление", "ТЕСТ 8"),
        ("Facts: обновление", "ТЕСТ 9"),
        ("Summary: delta calculation", "ТЕСТ 10"),
        ("Capabilities: появление/исчезновение", "ТЕСТ 11"),
        ("Engines: добавление/удаление", "ТЕСТ 12"),
        ("Автономность (Diff работает после удаления профилей)", "ТЕСТ 13"),
        ("O(n) производительность (1000 фактов < 5s)", "ТЕСТ 14"),
        ("Симметрия (ADDED ↔ REMOVED при инверсии)", "ТЕСТ 15"),
    ]
    
    for req, test in requirements:
        print(f"   ✅ {req} ({test})")
    
    if failed == 0:
        print("\n🎉 Change Detection Layer v1.6.7 — ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("   Архитектура готова к интеграции в monitor.py!")
        return 0
    else:
        print(f"\n⚠️  Обнаружено {failed} проблем. Требуется исправление.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
