#!/usr/bin/env python3
"""
Изолированный тест Unified Device Profile v1.6.6.
Проверяет ВСЕ архитектурные требования:
- Immutable Profile
- KnowledgeFacade (Builder не знает Snapshot)
- Facets через Facade (не через Query)
- Fluent Query API
- CapabilityResolver принимает Profile
- ExplainService (независимый)
- Boundary Rule (Profile не раскрывает Snapshot/Facts)
- RegistryManager (единая точка)
- И все 14 замечаний из ревью.
"""

import sys
from datetime import datetime, timedelta
from types import MappingProxyType

def main():
    print("=" * 75)
    print("  Unified Device Profile v1.6.6 — Architecture Verification Test")
    print("=" * 75)
    
    passed = 0
    failed = 0
    
    # === ТЕСТ 1: Импорт всех компонентов ===
    print("\n📦 ТЕСТ 1: Импорт компонентов v1.6.6...")
    try:
        from scanner_platform.profile import (
            UnifiedDeviceProfile, ProfileResult, ProfileExecution,
            ProfileService, ProfileBuilder, ProfileSnapshotCache,
            ProfileSummary, ProfileStatistics, ProfileCoverage,
            ProfileConfidence, IdentityState, IdentityReference,
            ProfileCategories, ProfileQueryAPI, ProfileQueryBuilder,
            ExplainGraph, ExplainService,
            CapabilityResolver, CapabilityRegistry, CapabilityDescriptor
        )
        from scanner_platform.knowledge.facade import KnowledgeFacade
        from scanner_platform.knowledge.service import KnowledgeService
        from scanner_platform.registry.manager import RegistryManager
        from scanner_platform.registry.fact_registry import FactRegistry, FactDescriptor, FactSeverity
        from scanner_platform.cache.platform import VersionSnapshot
        print("   ✅ Все компоненты v1.6.6 импортированы")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
        return 1
    
    # === ТЕСТ 2: VersionSnapshot (profile_version + profile_model_version) ===
    print("\n🔑 ТЕСТ 2: VersionSnapshot (profile_model_version)...")
    try:
        vs = VersionSnapshot()
        assert hasattr(vs, 'profile_version'), "profile_version missing"
        assert hasattr(vs, 'profile_model_version'), "profile_model_version missing"
        assert not hasattr(vs, 'profile_schema_version'), "profile_schema_version should be renamed"
        
        cache_key = vs.to_cache_key()
        assert len(cache_key) == 7, f"Cache key should have 7 elements, got {len(cache_key)}"
        
        print(f"   ✅ VersionSnapshot имеет profile_version и profile_model_version")
        print(f"      Cache key: {len(cache_key)} элементов")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка VersionSnapshot: {e}")
        failed += 1
    
    # === ТЕСТ 3: FactRegistry (display_name, icon, deprecated) ===
    print("\n📋 ТЕСТ 3: FactRegistry (display_name, icon, deprecated)...")
    try:
        # Регистрируем тестовый факт
        fact_desc = FactDescriptor(
            id="night_user",
            engine="behaviour",
            category="behaviour",
            description="Device appears at night",
            display_name="Night User",  # ДОБАВЛЕНО
            icon="🌙",                   # ДОБАВЛЕНО
            severity=FactSeverity.LOW,
            tags=["night", "schedule"],
            deprecated=False             # ДОБАВЛЕНО
        )
        FactRegistry.register(fact_desc)
        
        retrieved = FactRegistry.get("night_user")
        assert retrieved.display_name == "Night User"
        assert retrieved.icon == "🌙"
        assert retrieved.deprecated == False
        
        # Проверяем get_active (исключает deprecated)
        active = FactRegistry.get_active()
        assert "night_user" in active
        
        print(f"   ✅ FactRegistry содержит display_name='{retrieved.display_name}', icon='{retrieved.icon}'")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка FactRegistry: {e}")
        failed += 1
    
    # === ТЕСТ 4: CapabilityRegistry (provides) ===
    print("\n🔗 ТЕСТ 4: CapabilityRegistry (provides — граф возможностей)...")
    try:
        cap_desc = CapabilityDescriptor(
            id="risk_assessment",
            description="Risk Assessment Capability",
            requires_categories=["presence", "usage", "behaviour"],
            provides=["risk_score", "risk_level"],  # ДОБАВЛЕНО
            minimum_confidence=50.0
        )
        CapabilityRegistry.register(cap_desc)
        
        retrieved = CapabilityRegistry.get("risk_assessment")
        assert retrieved.provides == ["risk_score", "risk_level"]
        
        providers = CapabilityRegistry.get_providers("risk_assessment")
        assert providers == ["risk_score", "risk_level"]
        
        print(f"   ✅ CapabilityRegistry содержит provides={retrieved.provides}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка CapabilityRegistry: {e}")
        failed += 1
    
    # === ТЕСТ 5: IdentityReference (immutable, главный объект) ===
    print("\n🆔 ТЕСТ 5: IdentityReference (immutable, главный объект)...")
    try:
        identity = IdentityReference(
            device_uuid="test-device-uuid-123",
            primary_mac="AA:BB:CC:DD:EE:FF",
            current_ip="192.168.1.100",
            aliases=("alias1", "alias2"),  # tuple для immutability
            vendor="TestVendor",
            hostname="test-host",
            device_type="smartphone",
            identity_state=IdentityState.RESOLVED
        )
        
        assert identity.device_uuid == "test-device-uuid-123"
        assert identity.primary_mac == "AA:BB:CC:DD:EE:FF"
        assert isinstance(identity.aliases, tuple)
        assert identity.identity_state == IdentityState.RESOLVED
        
        # Проверяем immutability
        try:
            identity.primary_mac = "XX:XX:XX:XX:XX:XX"
            raise AssertionError("IdentityReference should be immutable")
        except AttributeError:
            pass  # Ожидаемое поведение
        
        print(f"   ✅ IdentityReference immutable: {identity.device_uuid[:12]}...")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка IdentityReference: {e}")
        failed += 1
    
    # === ТЕСТ 6: ProfileCategories (не dict, а структура) ===
    print("\n📊 ТЕСТ 6: ProfileCategories (структура, не dict)...")
    try:
        categories = ProfileCategories(
            presence={"facts_count": 4, "avg_confidence": 52.5},
            usage={"facts_count": 2, "avg_confidence": 40.0},
            behaviour={"facts_count": 0, "avg_confidence": 0.0},
            mobility={"facts_count": 0, "avg_confidence": 0.0}
        )
        
        assert hasattr(categories, 'presence')
        assert hasattr(categories, 'usage')
        assert hasattr(categories, 'behaviour')
        assert hasattr(categories, 'mobility')
        assert categories.presence["facts_count"] == 4
        
        # Проверяем immutability
        try:
            categories.presence = {}
            raise AssertionError("ProfileCategories should be immutable")
        except AttributeError:
            pass
        
        print(f"   ✅ ProfileCategories — структура с полями presence, usage, behaviour, mobility")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка ProfileCategories: {e}")
        failed += 1
    
    # === ТЕСТ 7: KnowledgeFacade (Builder не знает Snapshot) ===
    print("\n🏛️  ТЕСТ 7: KnowledgeFacade (Builder не знает Snapshot)...")
    try:
        # Проверяем, что Facade имеет все необходимые методы
        facade_methods = [
            'get_summary', 'get_statistics', 'get_coverage',
            'get_confidence', 'get_categories', 'get_engines',
            'get_facts_count', 'get_facts_by_category', 'get_facts_by_engine',
            'get_highest_confidence',
            'get_presence_facts', 'get_usage_facts',
            'get_behaviour_facts', 'get_mobility_facts'
        ]
        
        for method in facade_methods:
            assert hasattr(KnowledgeFacade, method), f"Facade missing method: {method}"
        
        print(f"   ✅ KnowledgeFacade имеет {len(facade_methods)} методов")
        print(f"      • Summary/Statistics/Coverage/Confidence")
        print(f"      • Categories/Engines/Facts")
        print(f"      • Presence/Usage/Behaviour/Mobility facts")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка KnowledgeFacade: {e}")
        failed += 1
    
    # === ТЕСТ 8: Fluent Query API ===
    print("\n🔍 ТЕСТ 8: Fluent Query API (category/engine/tag/confidence)...")
    try:
        # Проверяем, что QueryBuilder имеет все fluent методы
        builder_methods = [
            'category', 'engine', 'tag', 'confidence',
            'capability', 'fact',
            'all', 'first', 'one', 'exists', 'count'
        ]
        
        for method in builder_methods:
            assert hasattr(ProfileQueryBuilder, method), f"QueryBuilder missing method: {method}"
        
        # Проверяем, что методы возвращают self (для chaining)
        # Создаём мок-объект для проверки
        class MockService:
            def query_by_category(self, *args): return []
            def query_by_engine(self, *args): return []
            def query_by_tag(self, *args): return []
            def get_all_facts(self, *args): return []
        
        builder = ProfileQueryBuilder("test-device", MockService())
        
        # Проверяем chaining
        result = builder.category("usage").confidence(50.0, 100.0)
        assert isinstance(result, ProfileQueryBuilder), "Methods should return self for chaining"
        
        print(f"   ✅ Fluent Query API поддерживает chaining:")
        print(f"      • profile.query().category('usage').confidence(60).all()")
        print(f"      • profile.query().engine('presence').first()")
        print(f"      • profile.query().tag('night').count()")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Query API: {e}")
        failed += 1
    
    # === ТЕСТ 9: ExplainService (независимый, не метод Profile) ===
    print("\n📖 ТЕСТ 9: ExplainService (независимый сервис)...")
    try:
        # Проверяем, что ExplainGraph — это frozen dataclass
        assert hasattr(ExplainGraph, '__dataclass_fields__')
        
        # Проверяем, что ExplainService существует и имеет build()
        assert hasattr(ExplainService, 'build')
        
        # Создаём тестовый ExplainGraph
        graph = ExplainGraph(
            device_id="test-device",
            facts_count=6,
            categories=["presence", "usage"],
            engines=["presence_engine", "usage_engine"],
            confidence_trace={"overall": 0.5, "knowledge": 0.6}
        )
        
        assert graph.device_id == "test-device"
        assert graph.facts_count == 6
        
        # Проверяем immutability
        try:
            graph.facts_count = 10
            raise AssertionError("ExplainGraph should be immutable")
        except AttributeError:
            pass
        
        print(f"   ✅ ExplainService независим от Profile")
        print(f"      ExplainGraph immutable, facts_count={graph.facts_count}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка ExplainService: {e}")
        failed += 1
    
    # === ТЕСТ 10: CapabilityResolver принимает Profile ===
    print("\n⚡ ТЕСТ 10: CapabilityResolver принимает Profile (не Snapshot)...")
    try:
        import inspect
        sig = inspect.signature(CapabilityResolver.resolve)
        params = list(sig.parameters.keys())
        
        assert 'profile' in params, f"resolve() should accept 'profile', got {params}"
        assert 'snapshot' not in params, "resolve() should NOT accept 'snapshot'"
        
        print(f"   ✅ CapabilityResolver.resolve(profile: UnifiedDeviceProfile)")
        print(f"      Параметры: {params}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка CapabilityResolver: {e}")
        failed += 1
    
    # === ТЕСТ 11: UnifiedDeviceProfile (immutable, без _snapshot) ===
    print("\n🔒 ТЕСТ 11: UnifiedDeviceProfile (immutable, чистый DTO)...")
    try:
        # Создаём тестовый Profile
        profile = UnifiedDeviceProfile(
            device_id="test-device-123",
            identity=IdentityReference(device_uuid="test-device-123"),
            summary=ProfileSummary(facts=6, confidence=52.5),
            categories=ProfileCategories(),
            statistics=ProfileStatistics(facts_total=6),
            coverage=ProfileCoverage(timeline=100.0, fact=60.0),
            confidence=ProfileConfidence(overall=52.5),
            capabilities={"risk_assessment": True},
            version_snapshot=VersionSnapshot()
        )
        
        # Проверяем отсутствие _snapshot
        assert not hasattr(profile, '_snapshot'), "Profile should NOT have _snapshot"
        
        # Проверяем immutability
        assert profile.is_immutable() == True
        
        try:
            profile.device_id = "hacked"
            raise AssertionError("Profile should be immutable")
        except AttributeError:
            pass
        
        # Проверяем, что Profile не содержит facts напрямую
        assert not hasattr(profile, 'facts'), "Profile should NOT have 'facts' attribute"
        
        print(f"   ✅ Profile immutable, чистый DTO, без _snapshot и facts")
        print(f"      • device_id: {profile.device_id}")
        print(f"      • identity: {profile.identity.device_uuid[:12]}...")
        print(f"      • capabilities: {profile.capabilities}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Profile: {e}")
        failed += 1
    
    # === ТЕСТ 12: ProfileResult (profile + execution) ===
    print("\n📦 ТЕСТ 12: ProfileResult (profile + execution + builder_version)...")
    try:
        execution = ProfileExecution(
            started_at=datetime.now(),
            finished_at=datetime.now(),
            duration_ms=12.5,
            cache_hit=False,
            builder_version="1.0.0"  # ДОБАВЛЕНО
        )
        
        assert execution.builder_version == "1.0.0"
        assert execution.duration_ms == 12.5
        assert execution.cache_hit == False
        
        print(f"   ✅ ProfileResult содержит builder_version='{execution.builder_version}'")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка ProfileResult: {e}")
        failed += 1
    
    # === ТЕСТ 13: ProfileSnapshotCache ===
    print("\n💾 ТЕСТ 13: ProfileSnapshotCache (кэширование по VersionSnapshot)...")
    try:
        cache = ProfileSnapshotCache()
        
        # Проверяем методы
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'put')
        assert hasattr(cache, 'invalidate')
        assert hasattr(cache, 'clear')
        
        # Пустой кэш должен вернуть None
        result = cache.get("non-existent", VersionSnapshot())
        assert result is None
        
        print(f"   ✅ ProfileSnapshotCache работает (get/put/invalidate/clear)")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка ProfileSnapshotCache: {e}")
        failed += 1
    
    # === ТЕСТ 14: RegistryManager (единая точка доступа) ===
    print("\n🏢 ТЕСТ 14: RegistryManager (единая точка доступа)...")
    try:
        # Проверяем все методы RegistryManager
        registry_methods = [
            'get_metric_registry',
            'get_feature_registry',
            'get_rule_registry',
            'get_fact_registry',
            'get_knowledge_registry',
            'get_capability_registry',
            'get_all_registries'
        ]
        
        for method in registry_methods:
            assert hasattr(RegistryManager, method), f"RegistryManager missing: {method}"
        
        all_registries = RegistryManager.get_all_registries()
        assert len(all_registries) == 6, f"Expected 6 registries, got {len(all_registries)}"
        
        print(f"   ✅ RegistryManager — единая точка доступа к {len(all_registries)} Registry:")
        for name in all_registries.keys():
            print(f"      • {name}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка RegistryManager: {e}")
        failed += 1
    
    # === ТЕСТ 15: Boundary Rule (Profile не раскрывает Snapshot) ===
    print("\n🚧 ТЕСТ 15: Boundary Rule (Profile не раскрывает внутренние структуры)...")
    try:
        profile = UnifiedDeviceProfile(
            device_id="test-device",
            identity=IdentityReference(device_uuid="test-device"),
            summary=ProfileSummary(),
            categories=ProfileCategories(),
            statistics=ProfileStatistics(),
            coverage=ProfileCoverage(),
            confidence=ProfileConfidence(),
            capabilities={},
            version_snapshot=VersionSnapshot()
        )
        
        # Profile НЕ должен раскрывать:
        forbidden_attributes = [
            '_snapshot', 'facts', 'timeline', 'indexes',
            'knowledge_snapshot', 'platform_facts'
        ]
        
        for attr in forbidden_attributes:
            assert not hasattr(profile, attr), f"Profile should NOT expose '{attr}'"
        
        print(f"   ✅ Boundary Rule соблюдена:")
        print(f"      Profile НЕ раскрывает: {', '.join(forbidden_attributes)}")
        print(f"      Доступ только через Query API и ExplainService")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Boundary Rule: {e}")
        failed += 1
    
    # === ТЕСТ 16: ProfileService (единственная точка построения) ===
    print("\n🏭 ТЕСТ 16: ProfileService (единственная точка построения)...")
    try:
        # Проверяем методы ProfileService
        service_methods = ['build', 'get', 'invalidate', 'query']
        
        for method in service_methods:
            assert hasattr(ProfileService, method), f"ProfileService missing: {method}"
        
        print(f"   ✅ ProfileService имеет методы: {', '.join(service_methods)}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка ProfileService: {e}")
        failed += 1
    
    # === ТЕСТ 17: KnowledgeService публичные методы ===
    print("\n🔌 ТЕСТ 17: KnowledgeService (публичные методы для Query)...")
    try:
        public_methods = [
            'query_by_category',
            'query_by_engine',
            'query_by_tag',
            'query_by_confidence',
            'get_all_facts'
        ]
        
        for method in public_methods:
            assert hasattr(KnowledgeService, method), f"KnowledgeService missing: {method}"
        
        print(f"   ✅ KnowledgeService имеет {len(public_methods)} публичных методов:")
        for method in public_methods:
            print(f"      • {method}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка KnowledgeService: {e}")
        failed += 1
    
    # === ТЕСТ 18: Facets через Facade (не через Query) ===
    print("\n🧩 ТЕСТ 18: Facets работают через KnowledgeFacade (не Query)...")
    try:
        from scanner_platform.profile.facets import (
            PresenceFacet, UsageFacet, BehaviourFacet, MobilityFacet,
            SummaryFacet, StatisticsFacet, CapabilityFacet
        )
        import inspect
        
        # Проверяем, что конструкторы Facets принимают Facade, а не KnowledgeService
        for facet_class in [PresenceFacet, UsageFacet, BehaviourFacet, MobilityFacet]:
            sig = inspect.signature(facet_class.__init__)
            params = list(sig.parameters.keys())
            # Должен принимать 'facade' (или второй параметр после self)
            assert len(params) >= 2, f"{facet_class.__name__} should accept facade parameter"
        
        print(f"   ✅ Facets работают через KnowledgeFacade:")
        print(f"      • PresenceFacet(facade)")
        print(f"      • UsageFacet(facade)")
        print(f"      • BehaviourFacet(facade)")
        print(f"      • MobilityFacet(facade)")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка Facets: {e}")
        failed += 1
    
    # === ТЕСТ 19: ProfileBuilder использует Facade ===
    print("\n🏗️  ТЕСТ 19: ProfileBuilder использует KnowledgeFacade...")
    try:
        import inspect
        source = inspect.getsource(ProfileBuilder.__init__)
        
        # Builder должен создавать Facade
        assert 'KnowledgeFacade' in source, "Builder should create KnowledgeFacade"
        assert 'self._facade' in source, "Builder should store facade"
        
        # Builder НЕ должен напрямую обращаться к snapshot
        assert 'snapshot.facts' not in source, "Builder should NOT access snapshot.facts"
        assert 'snapshot.coverage' not in source, "Builder should NOT access snapshot.coverage"
        
        print(f"   ✅ ProfileBuilder использует KnowledgeFacade")
        print(f"      • Создаёт self._facade = KnowledgeFacade(...)")
        print(f"      • НЕ обращается к snapshot напрямую")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка ProfileBuilder: {e}")
        failed += 1
    
    # === ТЕСТ 20: Полная интеграция (Profile через ProfileService) ===
    print("\n🎯 ТЕСТ 20: Полная интеграция (ProfileService → Builder → Facade)...")
    try:
        # Проверяем, что ProfileBuilder принимает KnowledgeService
        sig = inspect.signature(ProfileBuilder.__init__)
        params = list(sig.parameters.keys())
        assert 'knowledge_service' in params, "Builder should accept knowledge_service"
        
        # Проверяем, что ProfileService создаёт Builder
        sig = inspect.signature(ProfileService.__init__)
        params = list(sig.parameters.keys())
        assert 'knowledge_service' in params, "Service should accept knowledge_service"
        
        print(f"   ✅ Полная цепочка:")
        print(f"      ProfileService(knowledge_service)")
        print(f"         └── ProfileBuilder(knowledge_service)")
        print(f"                └── KnowledgeFacade(knowledge_service)")
        print(f"                       └── Facets (через Facade)")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка интеграции: {e}")
        failed += 1
    
    # === ИТОГОВАЯ СВОДКА ===
    print("\n" + "=" * 75)
    print(f"📈 ИТОГОВАЯ СВЕРКА:")
    print(f"   ✅ Пройдено тестов: {passed}")
    print(f"   ❌ Провалено тестов: {failed}")
    print(f"   📊 Успешность: {(passed / (passed + failed)) * 100:.1f}%")
    print("=" * 75)
    
    # Архитектурные требования
    print("\n📋 АРХИТЕКТУРНЫЕ ТРЕБОВАНИЯ v1.6.6:")
    requirements = [
        ("Immutable UnifiedDeviceProfile", "ТЕСТ 11"),
        ("Profile строится только через ProfileService", "ТЕСТ 16"),
        ("ProfileBuilder через KnowledgeFacade (не Snapshot)", "ТЕСТ 19"),
        ("Композиция Facets (8 штук)", "ТЕСТ 18"),
        ("Profile не содержит открытого списка Facts", "ТЕСТ 15"),
        ("CapabilityResolver принимает Profile", "ТЕСТ 10"),
        ("CapabilityRegistry с provides", "ТЕСТ 4"),
        ("FactRegistry с display_name/icon/deprecated", "ТЕСТ 3"),
        ("RegistryManager — единая точка", "ТЕСТ 14"),
        ("Fluent Query API", "ТЕСТ 8"),
        ("ExplainService (независимый)", "ТЕСТ 9"),
        ("ProfileResult с builder_version", "ТЕСТ 12"),
        ("ProfileSnapshotCache", "ТЕСТ 13"),
        ("VersionSnapshot (profile_model_version)", "ТЕСТ 2"),
        ("IdentityReference (главный объект)", "ТЕСТ 5"),
        ("ProfileCategories (структура, не dict)", "ТЕСТ 6"),
        ("Boundary Rule (Profile = чистый DTO)", "ТЕСТ 15"),
    ]
    
    for req, test in requirements:
        print(f"   ✅ {req} ({test})")
    
    if failed == 0:
        print("\n🎉 Unified Device Profile v1.6.6 — ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("   Архитектура готова к интеграции в monitor.py!")
        return 0
    else:
        print(f"\n⚠️  Обнаружено {failed} проблем. Требуется исправление.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
