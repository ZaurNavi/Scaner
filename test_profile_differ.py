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
        
        print(f"
