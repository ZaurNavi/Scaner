#!/usr/bin/env python3
"""
Изолированный тест Knowledge Layer v1.6.5.
Проверяет все архитектурные исправления: immutable, lazy indexing, correct ID usage, etc.
"""

import sys
from datetime import datetime, timedelta
from types import MappingProxyType

def main():
    print("=" * 70)
    print("  Knowledge Layer v1.6.5 — Architecture Verification Test")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    # === ТЕСТ 1: Импорт всех компонентов ===
    print("\n📦 ТЕСТ 1: Импорт компонентов Knowledge Layer...")
    try:
        from scanner_platform.knowledge import (
            KnowledgeService, KnowledgeCache, KnowledgeSnapshot, KnowledgeQuery,
            KnowledgeRegistry, KnowledgeDescriptor, KnowledgeCategory,
            FactRegistry, FactDescriptor, FactSeverity
        )
        from scanner_platform.knowledge.indexes.fact_index import FactIndex
        from scanner_platform.knowledge.builders.summary import SummaryBuilder
        from scanner_platform.knowledge.builders.statistics import StatisticsBuilder
        from scanner_platform.knowledge.builders.coverage import CoverageBuilder
        from scanner_platform.cache.platform import VersionSnapshot
        from scanner_platform.core.base_engine import ExecutionInfo
        print("   ✅ Все компоненты импортированы успешно")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
        return 1

    # === ТЕСТ 2: Fact Registry и Knowledge Registry (engine, id, providers) ===
    print("\n📋 ТЕСТ 2: Fact Registry и Knowledge Registry...")
    try:
        # Проверяем FactDescriptor
        fact_desc = FactDescriptor(
            id="night_user",
            engine="behaviour",
            category="behaviour",
            description="Device appears at night",
            severity=FactSeverity.LOW,
            tags=["night", "schedule"]
        )
        FactRegistry.register(fact_desc)
        
        retrieved = FactRegistry.get("night_user")
        assert retrieved is not None, "Fact not found by ID"
        assert retrieved.engine == "behaviour", "Engine field missing"
        
        # Проверяем KnowledgeDescriptor
        know_desc = KnowledgeDescriptor(
            category=KnowledgeCategory.BEHAVIOUR,
            description="Behavioural patterns",
            providers=["history_service"],
            engines=["behaviour_engine"]
        )
        KnowledgeRegistry.register(know_desc)
        
        assert KnowledgeRegistry.get("behaviour").engines == ["behaviour_engine"]
        
        print("   ✅ Registry содержат engine, id, providers и engines")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Registry: {e}")
        failed += 1

    # === ТЕСТ 3: Lazy Indexing и корректный поиск по fact.id (не category!) ===
    print("\n🗂️  ТЕСТ 3: Fact Index (Lazy & correct ID lookup)...")
    try:
        class MockFact:
            def __init__(self, fid, engine, category, conf):
                self.id = fid
                self.engine = engine
                self.category = category
                self.confidence = conf
                self.generated_at = datetime.now()

        facts = [MockFact("night_user", "behaviour", "behaviour", 75.0)]
        index = FactIndex(facts)
        
        # Проверяем ленивость
        assert index._by_tag is None, "Index should be lazy (None initially)"
        
        # Триггерим построение тега
        tagged_facts = index.get_by_tag("night")
        assert len(tagged_facts) == 1, "Should find fact by tag"
        assert tagged_facts[0].id == "night_user"
        
        print("   ✅ Индексация ленивая и использует fact.id для поиска тегов")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Fact Index: {e}")
        failed += 1

    # === ТЕСТ 4: Snapshot действительно Immutable ===
    print("\n🔒 ТЕСТ 4: Knowledge Snapshot Immutability...")
    try:
        mock_facts = [MockFact("test_fact", "behaviour", "behaviour", 80.0)]
        summary_dict = {"facts_count": 1}
        stats_dict = {"facts_total": 1}
        
        from scanner_platform.coverage.platform import Coverage
        cov = Coverage(timeline_coverage=100, metric_coverage=100, feature_coverage=100, rule_coverage=100, fact_coverage=100)
        vs = VersionSnapshot()
        
        snapshot = KnowledgeSnapshot.create(
            device_id="test-dev",
            version_snapshot=vs,
            facts=mock_facts,
            summary=summary_dict,
            statistics=stats_dict,
            coverage=cov
        )
        
        assert snapshot.is_immutable() == True
        assert isinstance(snapshot.facts, tuple), "Facts must be tuple"
        assert isinstance(snapshot.summary, MappingProxyType), "Summary must be MappingProxyType"
        assert isinstance(snapshot.statistics, MappingProxyType), "Statistics must be MappingProxyType"
        
        # Попытка изменить должна вызвать ошибку
        try:
            snapshot.facts.append("hack")
            raise AssertionError("Should not be able to append to tuple")
        except AttributeError:
            pass # Ожидаемое поведение
            
        print("   ✅ Snapshot действительно immutable (tuple, MappingProxyType)")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Immutability: {e}")
        failed += 1

    # === ТЕСТ 5: Knowledge Query (Index usage, confidence_range, predicate) ===
    print("\n🔍 ТЕСТ 5: Knowledge Query (Index-first, advanced filters)...")
    try:
        # Создаем фейковый snapshot с индексом
        facts_list = [
            MockFact("f1", "behaviour", "behaviour", 90.0),
            MockFact("f2", "usage", "usage", 40.0),
            MockFact("f3", "behaviour", "behaviour", 60.0)
        ]
        # Регистрируем факты для тегов
        FactRegistry.register(FactDescriptor(id="f1", engine="behaviour", category="behaviour", description="t1", tags=["tag1"]))
        FactRegistry.register(FactDescriptor(id="f2", engine="usage", category="usage", description="t2", tags=["tag2"]))
        FactRegistry.register(FactDescriptor(id="f3", engine="behaviour", category="behaviour", description="t3", tags=["tag1"]))
        
        snap = KnowledgeSnapshot.create("dev", VersionSnapshot(), facts_list, {}, {}, cov)
        
        # Query по категории (должен использовать индекс)
        q1 = KnowledgeQuery(category="behaviour")
        res1 = q1.execute(snap)
        assert len(res1) == 2
        
        # Query по confidence_range
        q2 = KnowledgeQuery(confidence_range=(50.0, 95.0))
        res2 = q2.execute(snap)
        assert len(res2) == 2 # f1 (90) и f3 (60)
        
        # Query с predicate
        q3 = KnowledgeQuery(predicate=lambda f: f.id == "f2")
        res3 = q3.execute(snap)
        assert len(res3) == 1
        assert res3[0].id == "f2"
        
        print("   ✅ Query использует индексы, поддерживает range и predicate")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Query: {e}")
        failed += 1

    # === ТЕСТ 6: Coverage Builder (агрегация, не хардкод 100%) ===
    print("\n📊 ТЕСТ 6: Coverage Builder (Aggregation from EngineResults)...")
    try:
        class MockEngineResult:
            def __init__(self, cov):
                self.coverage = cov
                
        er1 = MockEngineResult(Coverage(50.0, 50.0, 50.0, 50.0, 50.0))
        er2 = MockEngineResult(Coverage(90.0, 90.0, 90.0, 90.0, 90.0))
        
        engine_results = {"behaviour": er1, "usage": er2}
        
        agg_cov = CoverageBuilder.build(engine_results)
        
        assert agg_cov.metric_coverage == 70.0, f"Expected 70.0, got {agg_cov.metric_coverage}"
        assert agg_cov.fact_coverage == 70.0
        
        print("   ✅ Coverage корректно агрегируется из EngineResults (не 100%)")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Coverage Builder: {e}")
        failed += 1

    # === ТЕСТ 7: Statistics Builder (нет coverage_average) ===
    print("\n📈 ТЕСТ 7: Statistics Builder (No coverage_average)...")
    try:
        stats = StatisticsBuilder.build([MockFact("f1", "b", "b", 80.0)])
        
        assert "coverage_average" not in stats, "coverage_average should not be in statistics"
        assert "average_confidence" in stats
        assert stats["average_confidence"] == 80.0
        
        print("   ✅ Statistics не содержит coverage_average")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Statistics Builder: {e}")
        failed += 1

    # === ТЕСТ 8: Knowledge Service использует отдельный Cache ===
    print("\n🗄️  ТЕСТ 8: Knowledge Service & Knowledge Cache separation...")
    try:
        service = KnowledgeService()
        
        # Проверяем, что внутри есть отдельный кэш
        assert hasattr(service, '_cache')
        assert isinstance(service._cache, KnowledgeCache)
        
        # Создаем и получаем
        service.create_snapshot("dev-123", [MockFact("f1", "b", "b", 90.0)])
        snap = service.get_snapshot("dev-123")
        
        assert snap is not None
        assert snap.device_id == "dev-123"
        
        print("   ✅ Service использует отдельный KnowledgeCache (не хранит сам)")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Service/Cache: {e}")
        failed += 1

    # === ТЕСТ 9: VersionSnapshot и ExecutionInfo ===
    print("\n⏱️  ТЕСТ 9: VersionSnapshot (knowledge_version) & ExecutionInfo...")
    try:
        vs = VersionSnapshot()
        assert hasattr(vs, 'knowledge_version'), "knowledge_version missing"
        assert vs.knowledge_version == "1.0.0"
        
        # Проверка ExecutionInfo
        exec_info = ExecutionInfo()
        assert hasattr(exec_info, 'started_at')
        assert hasattr(exec_info, 'finished_at')
        assert hasattr(exec_info, 'duration_ms')
        assert hasattr(exec_info, 'cache_hit')
        assert hasattr(exec_info, 'warnings')
        assert hasattr(exec_info, 'errors')
        
        print("   ✅ VersionSnapshot имеет knowledge_version, ExecutionInfo корректен")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Version/Execution: {e}")
        failed += 1

    # === ИТОГОВАЯ СВОДКА ===
    print("\n" + "=" * 70)
    print(f"📈 ИТОГОВАЯ СВЕРКА:")
    print(f"   ✅ Пройдено тестов: {passed}")
    print(f"   ❌ Провалено тестов: {failed}")
    print(f"   📊 Успешность: {(passed / (passed + failed)) * 100:.1f}%")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 Knowledge Layer v1.6.5 — ВСЕ АРХИТЕКТУРНЫЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("   Immutable, Lazy Indexing, Correct ID, Aggregated Coverage — всё работает.")
        print("   Готово к интеграции в monitor.py!")
        return 0
    else:
        print(f"\n⚠️  Обнаружено {failed} проблем. Требуется исправление.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
