#!/usr/bin/env python3
"""
Repeater Monitor
monitor.py

Главный модуль-оркестратор.
"""

from __future__ import annotations

import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

from config import App, Cisco, Network, Paths
from constants import DATE_FORMAT

from snmp import get_arp_table
from netflow import aggregate_netflow
from report import (
    build_devices,
    analyze_all,
    filter_devices,
    sort_devices,
    print_table,
    save_report,
    save_debug_json,
    enrich_device_metadata,
)
from fingerprint.analysis import fingerprint_all
from fingerprint.collectors.base import collect_all, CollectedData, FingerprintResult
from fingerprint.controllers.registry import get_controller_collectors
from storage.history import enrich
from storage.device_db import save_state

from storage.archivist import (
    DatabaseManager,
    Migrator,
    Repository,
    Archivist,
    build_snapshot_bundle,
)
from storage.schema import Scan, ScanStatus
from events import EventEngine
from history import HistoryService
from traffic import traffic_collector
from session import SessionEngine, SessionEndReason
from identity import IdentityService, IdentityRepository
from confidence import ConfidenceService, FactCategory
from behaviour import BehaviourService, BehaviourCategory
from mobility import MobilityService
from mobility.registry import ProviderRegistry as MobilityProviderRegistry
from mobility.providers.session_provider import SessionMetricsProvider
from mobility.features.roaming_feature import build_roaming_rate

# v1.6.1: Presence Engine импорты
from presence import PresenceService
from presence.registry import ProviderRegistry as PresenceProviderRegistry
from presence.providers.history_provider import HistoryProvider
from presence.features.visit_feature import build_history_depth_days
from presence.categories import EventType

# v1.6.2: Usage Engine импорты
from usage import UsageService
from usage.registry import ProviderRegistry as UsageProviderRegistry
from usage.providers.traffic_provider import TrafficProvider

# v1.6.3 + v1.6.4: Scanner Platform Core импорты
from scanner_platform import Pipeline, PlatformValidator, VersionSnapshot, DeviceState
from scanner_platform.core.platform import Platform

# v1.6.5: Knowledge Layer импорты
from scanner_platform.knowledge import (
    KnowledgeService, KnowledgeCache, KnowledgeSnapshot, KnowledgeQuery,
    KnowledgeRegistry, KnowledgeDescriptor, KnowledgeCategory,
    FactRegistry, FactDescriptor, FactSeverity
)

# v1.6.6: Unified Device Profile импорты
from scanner_platform.profile import ProfileService, ExplainService

# v1.6.7: Change Detection Layer импорты
from scanner_platform.diff import (
    ProfileDiffer, ProfileDiff, EMPTY_DIFF, ChangeType, CapabilityState,
    DifferentIdentityError, InvalidProfileError
)

# v1.6.8: Domain Event Layer импорты
from scanner_platform.events import (
    EventGenerator, DomainEventSet, EMPTY_EVENT_SET
)

# v1.6.9: Configuration Layer импорты
from configuration import get_config_manager


def print_header() -> None:
    print()
    print("=" * 60)
    print(f"  {App.NAME}  v{App.VERSION}")
    print(f"  {datetime.now().strftime(DATE_FORMAT)}")
    print("=" * 60)
    print()
    print(f"  Cisco   : {Cisco.IP}")
    print(f"  Network : {Network.SUBNET} ({Network.NAME})")
    print(f"  Dir     : {Paths.NFDUMP_DIR}")
    print()
    print("-" * 60)


def init_archivist():
    try:
        print("  [ARCHIVIST] Initializing storage...")
        db_path = Path("storage/archivist/sisu.db")
        db = DatabaseManager(db_path)
        Migrator(db.get_connection()).migrate()
        print("  [ARCHIVIST] ✅ Migration OK")

        repo = Repository(db)
        archivist = Archivist(repo)
        print("  [ARCHIVIST] ✅ Archivist initialized")

        scan = Scan(
            id=str(uuid.uuid4()),
            started_at=datetime.now(),
            collector_version=App.VERSION,
            status=ScanStatus.SUCCESS,
        )

        from storage.schema import SnapshotBundle
        empty_bundle = SnapshotBundle(scan_id=scan.id, snapshot=None, scan=scan)
        try:
            repo.save_bundle(empty_bundle)
        except Exception:
            pass

        return archivist, db, scan

    except Exception as exc:
        print(f"  [ARCHIVIST] ❌ Initialization failed: {exc}")
        print("  [ARCHIVIST] ⚠️  Continuing without archivist...")
        return None, None, None


def _safe_get(obj, attr, default=None):
    """Безопасное получение атрибута объекта."""
    return getattr(obj, attr, default)


def _safe_get_feature_value(features, feature_id):
    """Безопасное извлечение значения фичи из разных типов контейнеров."""
    if not features:
        return None
    
    if isinstance(features, dict):
        feature = features.get(feature_id)
        if feature and hasattr(feature, 'value'):
            return feature
        return feature
    
    if hasattr(features, feature_id):
        value = getattr(features, feature_id)
        if value is not None:
            return type('FeatureWrapper', (), {
                'name': feature_id,
                'value': value,
                'unit': _get_unit_for_feature(feature_id)
            })()
    
    return None


def _get_unit_for_feature(feature_id: str) -> str:
    """Возвращает единицу измерения для известных фич."""
    units = {
        'average_session_duration': 'sec',
        'session_count': 'sessions',
        'total_session_duration': 'sec',
        'peak_speed': 'Mbps',
        'average_speed': 'Mbps',
        'total_traffic': 'bytes',
        'idle_ratio': 'ratio',
        'active_ratio': 'ratio',
        'ap_changes': 'changes',
        'ssid_changes': 'changes',
        'rssi_variance': 'dB',
        'snr_variance': 'dB',
        'lifetime_seconds': 'sec',
        'daily_presence': 'ratio',
        'active_hours': 'hours',
        'appearance_frequency': 'visits'
    }
    return units.get(feature_id, '')


def _safe_get_metric_value(metrics, metric_id):
    """Безопасное извлечение значения метрики."""
    if not metrics:
        return 0
    
    if hasattr(metrics, 'metrics') and isinstance(metrics.metrics, dict):
        metric = metrics.metrics.get(metric_id)
        if metric and hasattr(metric, 'value'):
            return metric.value
    
    if isinstance(metrics, dict):
        metric = metrics.get(metric_id)
        if metric:
            if hasattr(metric, 'value'):
                return metric.value
            return metric
    
    return 0


def _format_engine_output(engine_name: str, profile, debug_info, engine_type: str = "generic"):
    """Единый форматтер вывода для всех аналитических движков."""
    print(f"\n  [{engine_name}] Analyzing {engine_type}...")
    if not profile:
        print(f"      ❌ {engine_name} Profile not generated.")
        return

    identity_id = _safe_get(profile, 'identity_id', 'unknown')
    print(f"      ✅ {engine_name} Profile for {identity_id[:8]}...")
    
    print("         Coverage:")
    metric_coverage = _safe_get(profile, 'metric_coverage')
    if metric_coverage is not None:
        print(f"            • Metric Coverage: {metric_coverage:.1f}%")
    
    feature_coverage = _safe_get(profile, 'feature_coverage', 0.0)
    print(f"            • Feature Coverage: {feature_coverage:.1f}%")
    
    ratio_name = "Rule Match Ratio" if hasattr(profile, 'rule_match_ratio') else "Engine Coverage"
    ratio_val = _safe_get(profile, 'rule_match_ratio', feature_coverage)
    print(f"            • {ratio_name}: {ratio_val:.1f}%")

    timeline = _safe_get(profile, 'timeline')
    if timeline and hasattr(timeline, 'events') and timeline.events:
        events_count = len(timeline.events)
        sessions_count = 0
        if hasattr(timeline, 'count_by_type'):
            try:
                sessions_count = timeline.count_by_type(EventType.SESSION_STARTED)
            except Exception:
                sessions_count = 0
        
        metrics = _safe_get(profile, 'metrics')
        days_covered = _safe_get_metric_value(metrics, 'visit_count')
        
        print("         Timeline:")
        print(f"            • Events: {events_count}")
        print(f"            • Days Covered: {days_covered}")
        print(f"            • Sessions: {sessions_count}")
        print(f"            • Completeness: {feature_coverage:.1f}%")

    facts = _safe_get(profile, 'facts', [])
    features = _safe_get(profile, 'features')
    
    print(f"         Detected Facts ({len(facts)}):")
    
    for fact in facts:
        category_value = _safe_get(fact, 'category')
        if hasattr(category_value, 'value'):
            category_value = category_value.value
        
        fact_feature = _safe_get(fact, 'feature', '')
        feature_detail = _safe_get_feature_value(features, fact_feature)
        matched_rules = _safe_get(fact, 'matched_rules', [])
        
        if feature_detail and hasattr(feature_detail, 'name'):
            name = _safe_get(feature_detail, 'name', '')
            value = _safe_get(feature_detail, 'value', 'N/A')
            unit = _safe_get(feature_detail, 'unit', '')
            score = _safe_get(fact, 'score', _safe_get(fact, 'raw_score', 0))
            print(f"            • {category_value}: {name} = {value} {unit} (Score: {score}, Rule: {', '.join(matched_rules)})")
        else:
            measured_value = _safe_get(fact, 'measured_value', 'N/A')
            score = _safe_get(fact, 'score', _safe_get(fact, 'raw_score', 0))
            print(f"            • {category_value}: {measured_value} (Score: {score}, Rule: {', '.join(matched_rules)})")

    if facts:
        print("         Explain Summary:")
        for fact in facts:
            category_value = _safe_get(fact, 'category')
            if hasattr(category_value, 'value'):
                category_value = category_value.value
            
            fact_feature = _safe_get(fact, 'feature', '')
            feature_detail = _safe_get_feature_value(features, fact_feature)
            matched_rules = _safe_get(fact, 'matched_rules', [])
            
            if feature_detail and hasattr(feature_detail, 'name'):
                name = _safe_get(feature_detail, 'name', '')
                value = _safe_get(feature_detail, 'value', 'N/A')
                unit = _safe_get(feature_detail, 'unit', '')
                print(f"            • {category_value} because {name} = {value} {unit}, matched: {', '.join(matched_rules)}")
            else:
                measured_value = _safe_get(fact, 'measured_value', 'N/A')
                print(f"            • {category_value} because measured = {measured_value}, matched: {', '.join(matched_rules)}")

    if debug_info:
        print("         Performance & Debug:")
        cache_hit = _safe_get(debug_info, 'cache_hit', 'N/A')
        cache_key = _safe_get(debug_info, 'cache_key', 'N/A')
        print(f"            [Cache] Hit: {cache_hit} | Key: {cache_key}")
        
        eng_v = _safe_get(debug_info, 'engine_version', 'N/A')
        feat_v = _safe_get(debug_info, 'feature_version', 'N/A')
        prov_v = _safe_get(debug_info, 'provider_version', 'N/A')
        print(f"            [Versions] Engine: {eng_v} | Feature: {feat_v} | Provider: {prov_v}")
        
        timing_parts = [f"Total: {_safe_get(debug_info, 'computation_time_ms', 0):.2f}ms"]
        prov_times = _safe_get(debug_info, 'provider_times', {})
        if prov_times:
            timing_parts.append(f"Providers: {', '.join([f'{k}={v:.2f}ms' for k, v in prov_times.items()])}")
        build_times = _safe_get(debug_info, 'builder_times', {})
        if build_times:
            timing_parts.append(f"Builders: {', '.join([f'{k}={v:.2f}ms' for k, v in build_times.items()])}")
        feat_times = _safe_get(debug_info, 'feature_times', {})
        if feat_times:
            timing_parts.append(f"Features: {', '.join([f'{k}={v:.2f}ms' for k, v in list(feat_times.items())[:2]])}")
            
        print(f"            [Timing] {' | '.join(timing_parts)}")
        
        skipped = _safe_get(debug_info, 'skipped_rules', [])
        if skipped:
            print(f"            [Skipped] Rules: {', '.join(skipped[:2])}{'...' if len(skipped) > 2 else ''}")
        missing = _safe_get(debug_info, 'missing_features', [])
        if missing:
            print(f"            [Missing] Features: {', '.join(missing)}")


def _format_knowledge_output(snapshot: KnowledgeSnapshot, query_results: dict):
    """Форматтер вывода для Knowledge Snapshot."""
    print(f"\n  [KNOWLEDGE] Building Knowledge Snapshot...")
    if not snapshot:
        print(f"      ❌ Knowledge Snapshot not generated.")
        return
    
    print(f"      ✅ Knowledge Snapshot for {snapshot.device_id[:8]}...")
    
    # Summary
    print("         Summary:")
    summary = snapshot.summary
    known_since = summary.get('known_since')
    known_since_str = known_since.strftime("%Y-%m-%d %H:%M") if known_since else "N/A"
    print(f"            • Known Since: {known_since_str}")
    print(f"            • History Depth: {summary.get('history_depth', 0)} days")
    print(f"            • Facts Count: {summary.get('facts_count', 0)}")
    print(f"            • Categories: {', '.join(summary.get('categories', [])) or 'none'}")
    print(f"            • Avg Confidence: {summary.get('average_confidence', 0):.1f}%")
    
    # Statistics
    print("         Statistics:")
    stats = snapshot.statistics
    print(f"            • Facts Total: {stats.get('facts_total', 0)}")
    print(f"            • Highest Confidence: {stats.get('highest_confidence', 0):.1f}%")
    by_cat = stats.get('facts_by_category', {})
    if by_cat:
        cat_str = ', '.join([f"{k}={v}" for k, v in by_cat.items()])
        print(f"            • By Category: {cat_str}")
    
    # Coverage
    print("         Coverage:")
    cov = snapshot.coverage
    print(f"            • Timeline: {cov.timeline_coverage:.1f}%")
    print(f"            • Metric: {cov.metric_coverage:.1f}%")
    print(f"            • Feature: {cov.feature_coverage:.1f}%")
    print(f"            • Rule: {cov.rule_coverage:.1f}%")
    print(f"            • Fact: {cov.fact_coverage:.1f}%")
    
    # Indexes
    print("         Indexes:")
    idx = snapshot.indexes
    print(f"            • By Category: {list(idx._by_category.keys()) if idx._by_category else 'lazy'}")
    print(f"            • By Engine: {list(idx._by_engine.keys()) if idx._by_engine else 'lazy'}")
    print(f"            • By Tag: {list(idx._by_tag.keys()) if idx._by_tag else 'lazy'}")
    
    # Query Results
    if query_results:
        print("         Query Results:")
        for query_name, results in query_results.items():
            print(f"            • {query_name}: {len(results)} facts")
    
    # Version
    print("         Version:")
    vs = snapshot.version_snapshot
    print(f"            • Timeline: {vs.timeline_version}")
    print(f"            • Metric Registry: {vs.metric_registry_version}")
    print(f"            • Feature Registry: {vs.feature_registry_version}")
    print(f"            • Rule Registry: {vs.rule_registry_version}")
    print(f"            • Engine: {vs.engine_version}")
    print(f"            • Knowledge: {vs.knowledge_version}")


def main() -> int:
    start = time.time()
    print_header()

    # === v1.6.9: Configuration Layer Initialization ===
    print("\n  [CONFIG] Initializing Configuration Layer...")
    try:
        config = get_config_manager()
        config.load({})  # Загружаем defaults
        config.validate()
        config.freeze()  # Делаем immutable для runtime
        
        print("  [CONFIG] ✅ Configuration loaded, validated and frozen")
        print(f"         • Monitor scan interval: {config.get('monitor.scan_interval')}s")
        print(f"         • SNMP enabled: {config.get('snmp.enabled')}")
        print(f"         • NetFlow enabled: {config.get('netflow.enabled')}")
        print(f"         • Fingerprint min confidence: {config.get('fingerprint.minimum_confidence')}")
        print(f"         • Knowledge cache size: {config.get('knowledge.cache_size')}")
        print(f"         • Events enabled: {config.get('events.events_enabled')}")
        print(f"         • Log level: {config.get('logging.level')}")
    except Exception as exc:
        print(f"  [CONFIG] ❌ Configuration initialization failed: {exc}")
        print("  [CONFIG] ⚠️  Continuing with fallback defaults...")

    # === v1.6.3: Scanner Platform Validation ===
    print("\n  [PLATFORM] Validating Scanner Platform Core...")
    try:
        validation_errors = PlatformValidator.validate_all()
        if validation_errors:
            print("  [PLATFORM] ❌ Validation failed:")
            for err in validation_errors:
                print(f"      • {err}")
            print("  [PLATFORM] ⚠️ Continuing without platform features...")
        else:
            print("  [PLATFORM] ✅ Scanner Platform Core validated successfully!")
    except Exception as exc:
        print(f"  [PLATFORM] ❌ Validation error: {exc}")
        print("  [PLATFORM] ⚠️ Continuing without platform features...")

    archivist, db, scan = init_archivist()
    
    # === v1.5.1: Инициализация History Service ===
    history_service = None
    if db:
        try:
            history_service = HistoryService(db.get_connection())
            print("  [HISTORY] ✅ History Service initialized")
        except Exception as exc:
            print(f"  [HISTORY] ❌ History Service initialization failed: {exc}")

    print("  [1/4]  Получение ARP-таблицы через SNMP...")
    try:
        arp = get_arp_table()
    except Exception as exc:
        print()
        print(f"  ❌  Ошибка SNMP: {exc}")
        print()
        return 1

    print(f"         Найдено устройств: {len(arp)}")
    if not arp:
        print()
        print("  ❌  Получена пустая ARP-таблица.")
        print()
        return 1

    print("  [2/4]  Агрегация NetFlow...")
    try:
        netflow = aggregate_netflow()
    except Exception as exc:
        print()
        print(f"  ❌  Ошибка NetFlow: {exc}")
        print()
        return 1

    print(f"         Активных IP: {len(netflow)}")

    print("  [3/4]  Формирование отчёта...")
    devices = build_devices(arp, netflow)
    enrich(devices)

    ips = [d.ip for d in devices]
    collected_data = collect_all(ips, devices)

    # ==============================================================================
    # v1.5.2: Traffic Collector Integration
    # ==============================================================================
    print("\n  [TRAFFIC] Initializing Traffic Collector...")
    traffic_data = traffic_collector.collect_all(ips)
    
    for ip in ips:
        if ip not in collected_data:
            collected_data[ip] = CollectedData()
        if ip in traffic_data:
            traffic_info = traffic_data[ip]
            traffic_result = FingerprintResult(
                source="traffic",
                raw_data={"responded": True, **traffic_info.to_dict()},
                elapsed_ms=0.0,
                confidence=100,
                capabilities=["traffic_monitored"]
            )
            collected_data[ip].sources["traffic"] = traffic_result

    # ==============================================================================
    # v1.4.9.1: Infrastructure Controller Integration (Omada Metadata)
    # ==============================================================================
    controller_collectors = get_controller_collectors()
    if controller_collectors:
        print("\n  [CONTROLLERS] Fetching infrastructure data...")
        for collector in controller_collectors:
            print(f"  [CONTROLLERS] Running {collector.name.capitalize()} Collector...")
            controller_data = collector.collect()
            
            if "error" in controller_data:
                print(f"  [CONTROLLERS] ❌ {collector.name} failed: {controller_data['error']}")
                continue

            omada_entities = {}
            for entity in controller_data.get("clients", []) + controller_data.get("devices", []):
                entity_ip = entity.get("ip")
                mac = entity.get("mac", "").replace("-", ":").upper()
                
                if entity_ip:
                    key = entity_ip
                else:
                    target_device = next((d for d in devices if d.mac and d.mac.upper() == mac), None)
                    key = target_device.ip if target_device else f"mac:{mac}"

                if key not in omada_entities:
                    omada_entities[key] = []
                omada_entities[key].append(entity)

            merged_count = 0
            for key, entities in omada_entities.items():
                if key.startswith("mac:"):
                    continue
                if key not in collected_data:
                    collected_data[key] = CollectedData()
                
                omada_result = FingerprintResult(
                    source="omada",
                    raw_data={"responded": True, "entities": entities},
                    elapsed_ms=0.0,
                    confidence=100,
                    capabilities=["managed_by_omada"]
                )
                collected_data[key].sources["omada"] = omada_result
                merged_count += 1
                
            print(f"  [CONTROLLERS] ✅ {collector.name.capitalize()} data merged into {merged_count} entities.")

    devices = fingerprint_all(devices, collected_data)
    enrich_device_metadata(devices, collected_data)
    analyze_all(devices)
    save_debug_json(devices, collected_data)

    # === v1.4.0 + ... + v1.6.9.2 ===
    if archivist and scan:
        print()
        print("  [ARCHIVIST] Saving bundles...")

        event_engine = EventEngine(Repository(db))
        from events import EventRepository, EventPersister
        event_repo = EventRepository(db)
        event_persister = EventPersister(event_repo)

        all_events = []
        total_event_elapsed_ms = 0.0
        total_persisted = 0
        first_device_id = None
        ip_to_device_id = {}

        for device in devices:
            collected = collected_data.get(device.ip, CollectedData())
            bundle = build_snapshot_bundle(device, scan, collected)
            result = archivist.save(bundle)

            if result.success:
                print(f"      💾 Saved bundle: {device.ip} ({result.observations_saved} obs, {result.evidence_saved} ev)")
                ip_to_device_id[device.ip] = result.device_id
                if first_device_id is None:
                    first_device_id = result.device_id

                current_snapshot_dict = {
                    "id": bundle.snapshot.id,
                    "device_id": result.device_id,
                    "ip": bundle.snapshot.ip,
                    "hostname": bundle.snapshot.hostname,
                    "device_type": bundle.snapshot.device_type.value,
                    "vendor": device.vendor or "",
                }

                event_result = event_engine.analyze(result.device_id, current_snapshot_dict)
                all_events.extend(event_result.events)
                total_event_elapsed_ms += event_result.elapsed_ms

                if event_result.events:
                    persist_result = event_persister.persist(event_result.events)
                    if persist_result.success:
                        total_persisted += persist_result.saved
            else:
                print(f"      ❌ Failed: {device.ip} — {result.error_message}")

        # === v1.5.3: Session Engine ===
        session_engine = None
        if history_service and db:
            try:
                session_engine = SessionEngine(history_service, Repository(db))
                print("\n  [SESSION] ✅ Session Engine initialized (with Recovery)")
                print("  [SESSION] Processing new snapshots...")
                for ip, device_id in ip_to_device_id.items():
                    snapshots = history_service.get_snapshots(device_id)
                    if snapshots:
                        snap_dicts = [{"timestamp": s.timestamp.isoformat(), "ip": s.ip, "hostname": s.hostname} for s in snapshots]
                        session_engine.process_snapshots(device_id, snap_dicts)
                
                if first_device_id:
                    active_sess = session_engine.get_active_session(first_device_id)
                    if active_sess:
                        print(f"      ✅ Active Session for {first_device_id[:8]}... (Duration: {active_sess.duration or 0:.0f}s, Snapshots: {active_sess.snapshots_count})")
                    else:
                        print("      ℹ️ No active session (device might be in timeout).")
            except Exception as exc:
                print(f"  [SESSION] ❌ Initialization/Processing failed: {exc}")

        # === v1.5.4: Identity Engine ===
        identity_service = None
        profiles = []
        if history_service and db:
            try:
                identity_repo = IdentityRepository(db)
                identity_service = IdentityService(history_service, identity_repo)
                print("\n  [IDENTITY] Building identities...")
                profiles = identity_service.refresh_all(list(ip_to_device_id.values()))
                print(f"      ✅ Built {len(profiles)} identities")
                if profiles:
                    sample = profiles[0]
                    print(f"      Sample Identity: {sample.device_id[:8]}... | MAC: {sample.primary_mac} | IPs: {len(sample.network.known_ips)} | APs: {len(sample.network.known_aps)}")
            except Exception as exc:
                print(f"  [IDENTITY] ❌ Failed: {exc}")

                # === v1.5.5 + v1.6.9.5: Confidence Service (with DI) ===
        if identity_service and profiles:
            try:
                # v1.6.9.5: Выводим информацию из Configuration Layer
                print("\n  [CONFIDENCE] Configuration from Configuration Layer:")
                print(f"         • Confidence enabled: {config.get('confidence.enabled', True)}")
                print(f"         • Max score: {config.get('confidence.max_score', 100)}")
                
                # v1.6.9.5: Передаём configuration через Dependency Injection
                confidence_service = ConfidenceService(
                    identity_service=identity_service,
                    configuration=config  # v1.6.9.5: DI
                )
                
                sample_device_id = profiles[0].device_id
                cp = confidence_service.get_profile(sample_device_id)
                
                if cp:
                    print(f"\n  [CONFIDENCE] Evaluating confidence...")
                    print(f"      ✅ Confidence Profile for {sample_device_id[:8]}...")
                    print(f"         Coverage: {cp.coverage:.1f}% | Facts: {cp.statistics.total_facts} | Evaluated: {cp.statistics.evaluated}")
                    if cp.summary.vendor:
                        print(f"         Best Vendor: {cp.summary.vendor.value} ({cp.summary.vendor.confidence:.1f}%)")
            except Exception as exc:
                print(f"  [CONFIDENCE] ❌ Failed: {exc}")

              # === v1.6.4 + v1.6.9.2: Behaviour Engine (Platform Core with DI) ===
        behaviour_engine_result = None
        if identity_service and profiles:
            try:
                from scanner_platform.behaviour.engine import BehaviourEngine

                sample_device_id = profiles[0].device_id
                
                # v1.6.9.2: Выводим информацию из Configuration Layer
                print("\n  [PLATFORM] Configuration from Configuration Layer:")
                print(f"         • Platform enabled: {config.get('platform.enabled', True)}")
                print(f"         • Behaviour enabled: {config.get('behaviour.enabled', True)}")
                print(f"         • Behaviour min confidence: {config.get('behaviour.min_confidence', 0.4)}")
                print(f"         • Fingerprint min confidence: {config.get('fingerprint.minimum_confidence')}")
                print(f"         • Knowledge cache size: {config.get('knowledge.cache_size')}")
                
                # v1.6.9.2: Создаём Platform instance с Dependency Injection
                platform = Platform(configuration=config)
                platform.start()
                
                # v1.6.9.2: Создаём BehaviourEngine с правильными аргументами
                # (соответствует оригинальной сигнатуре из behaviour/engine.py)
                behaviour_engine = BehaviourEngine(
                    history_service=history_service,
                    identity_service=identity_service,
                    session_engine=session_engine
                )
                
                # v1.6.9.2: Запускаем анализ через правильный метод analyze()
                behaviour_profile, debug_info = behaviour_engine.analyze(sample_device_id)
                
                # Адаптируем результат для _format_engine_output
                class BehaviourResultAdapter:
                    def __init__(self, profile, debug):
                        self.identity_id = profile.identity_id
                        self.metric_coverage = profile.metric_coverage
                        self.feature_coverage = profile.feature_coverage
                        self.rule_match_ratio = profile.rule_match_ratio
                        self.timeline = None  # Behaviour не имеет timeline
                        self.metrics = None
                        self.features = profile.features
                        self.facts = profile.facts

                adapter = BehaviourResultAdapter(behaviour_profile, debug_info)
                
                # Сохраняем для последующего использования в Profile Layer
                behaviour_engine_result = behaviour_profile
                
                _format_engine_output("BEHAVIOUR", adapter, debug_info, engine_type="behavioural patterns (Platform Core)")
                
            except Exception as exc:
                print(f"  [BEHAVIOUR] ❌ Failed: {exc}")
                import traceback
                traceback.print_exc()

        # === v1.5.7: Mobility Engine ===
        mobility_profile = None
        mobility_service = None
        if identity_service and profiles:
            try:
                MobilityProviderRegistry.register("session_provider", SessionMetricsProvider)
                mobility_service = MobilityService(identity_service, session_engine, history_service)
                sample_device_id = profiles[0].device_id
                mobility_profile = mobility_service.get_profile(sample_device_id)
                md = mobility_service.debug(sample_device_id) if hasattr(mobility_service, 'debug') else None
                _format_engine_output("MOBILITY", mobility_profile, md, engine_type="movement patterns")
            except Exception as exc:
                print(f"  [MOBILITY] ❌ Failed: {exc}")

        # === v1.6.1: Presence Engine ===
        presence_profile = None
        presence_service = None
        if history_service and profiles:
            try:
                PresenceProviderRegistry.register("history_provider", HistoryProvider, version="1.0.0", priority=10, dependencies=[])
                presence_service = PresenceService(history_service)
                sample_device_id = profiles[0].device_id
                presence_profile = presence_service.get_profile(sample_device_id)
                pd = presence_service.debug(sample_device_id) if hasattr(presence_service, 'debug') else None
                _format_engine_output("PRESENCE", presence_profile, pd, engine_type="temporal presence")
            except Exception as exc:
                print(f"  [PRESENCE] ❌ Failed: {exc}")

        # === v1.6.2: Usage Engine ===
        usage_profile = None
        usage_service = None
        if history_service and profiles:
            try:
                UsageProviderRegistry.register("traffic_provider", TrafficProvider, version="1.0.0", priority=10, dependencies=[])
                usage_service = UsageService(history_service)
                sample_device_id = profiles[0].device_id
                usage_profile = usage_service.get_profile(sample_device_id)
                ud = usage_service.debug(sample_device_id) if hasattr(usage_service, 'debug') else None
                _format_engine_output("USAGE", usage_profile, ud, engine_type="network usage patterns")
            except Exception as exc:
                print(f"  [USAGE] ❌ Failed: {exc}")
                import traceback
                traceback.print_exc()

                # === v1.6.5 + v1.6.6 + v1.6.7 + v1.6.8: Knowledge, Profile, Diff & Events ===
        if profiles and (behaviour_engine_result or mobility_profile or presence_profile or usage_profile):
            try:
                from scanner_platform.facts.models import Fact, FactStatus
                
                sample_device_id = profiles[0].device_id
                
                # === АДАПТЕР: Превращаем legacy-факты в Platform Facts ===
                def adapt_to_platform_fact(legacy_fact, engine_name: str) -> Fact:
                    if hasattr(legacy_fact, 'id') and hasattr(legacy_fact, 'engine'):
                        return legacy_fact
                    
                    category_value = legacy_fact.category
                    if hasattr(category_value, 'value'):
                        category_value = category_value.value
                    
                    confidence = getattr(legacy_fact, 'confidence', 0.0)
                    status = FactStatus.HIGH if confidence >= 60 else FactStatus.MEDIUM if confidence >= 40 else FactStatus.LOW
                    
                    matched_rules = getattr(legacy_fact, 'matched_rules', [])
                    if isinstance(matched_rules, list):
                        matched_rules = [r if isinstance(r, str) else str(r) for r in matched_rules]
                    
                    feature_name = getattr(legacy_fact, 'feature', '')
                    
                    return Fact(
                        id=str(uuid.uuid4()),
                        engine=engine_name,
                        category=category_value,
                        status=status,
                        confidence=confidence,
                        quality=0.9,
                        sources=[engine_name],
                        matched_rules=matched_rules,
                        matched_features=[feature_name] if feature_name else [],
                        explain={
                            "legacy": True,
                            "original_category": category_value,
                            "original_feature": feature_name,
                            "original_measured_value": getattr(legacy_fact, 'measured_value', None)
                        }
                    )
                
                # Собираем все Platform Facts из движков
                all_facts = []
                engine_results = {}
                
                if behaviour_engine_result:
                    # v1.6.9.2: ИСПРАВЛЕНО — адаптируем BehaviourFact в Fact
                    all_facts.extend([adapt_to_platform_fact(f, "behaviour") for f in behaviour_engine_result.facts])
                    engine_results["behaviour"] = behaviour_engine_result
                
                if mobility_profile and hasattr(mobility_profile, 'facts'):
                    all_facts.extend([adapt_to_platform_fact(f, "mobility") for f in mobility_profile.facts])
                    mock_mobility = type('obj', (object,), {'coverage': type('obj', (object,), {
                        'timeline_coverage': 100.0, 'metric_coverage': _safe_get(mobility_profile, 'metric_coverage', 0.0),
                        'feature_coverage': _safe_get(mobility_profile, 'feature_coverage', 0.0),
                        'rule_coverage': _safe_get(mobility_profile, 'mobility_coverage', 0.0), 'fact_coverage': 0.0
                    })()})()
                    engine_results["mobility"] = mock_mobility
                
                if presence_profile and hasattr(presence_profile, 'facts'):
                    all_facts.extend([adapt_to_platform_fact(f, "presence") for f in presence_profile.facts])
                    mock_presence = type('obj', (object,), {'coverage': type('obj', (object,), {
                        'timeline_coverage': 100.0, 'metric_coverage': _safe_get(presence_profile, 'metric_coverage', 0.0),
                        'feature_coverage': _safe_get(presence_profile, 'feature_coverage', 0.0),
                        'rule_coverage': _safe_get(presence_profile, 'rule_match_ratio', 0.0), 'fact_coverage': 0.0
                    })()})()
                    engine_results["presence"] = mock_presence
                
                if usage_profile and hasattr(usage_profile, 'facts'):
                    all_facts.extend([adapt_to_platform_fact(f, "usage") for f in usage_profile.facts])
                    mock_usage = type('obj', (object,), {'coverage': type('obj', (object,), {
                        'timeline_coverage': 100.0, 'metric_coverage': _safe_get(usage_profile, 'metric_coverage', 0.0),
                        'feature_coverage': _safe_get(usage_profile, 'feature_coverage', 0.0),
                        'rule_coverage': _safe_get(usage_profile, 'rule_match_ratio', 0.0), 'fact_coverage': 0.0
                    })()})()
                    engine_results["usage"] = mock_usage
                
                # 1. Создаём Knowledge Snapshot
                knowledge_service = KnowledgeService()
                knowledge_service.create_snapshot(
                    device_id=sample_device_id,
                    facts=all_facts,
                    engine_results=engine_results,
                    version_snapshot=VersionSnapshot(),
                    history_service=history_service
                )
                
                # 2. Строим Unified Device Profile через ProfileService
                profile_service = ProfileService(knowledge_service)
                profile_result = profile_service.build(sample_device_id, VersionSnapshot())
                profile = profile_result.profile
                
                # 3. Выводим Unified Device Profile
                print(f"\n  [PROFILE] Building Unified Device Profile...")
                print(f"      ✅ Profile built for {profile.device_id[:8]}... (Duration: {profile_result.execution.duration_ms:.2f}ms, Cache: {profile_result.execution.cache_hit})")
                
                print("         Identity:")
                print(f"            • UUID: {profile.identity.device_uuid[:8]}...")
                print(f"            • MAC: {profile.identity.primary_mac or 'N/A'}")
                print(f"            • IP: {profile.identity.current_ip or 'N/A'}")
                print(f"            • State: {profile.identity.identity_state.value}")
                
                print("         Summary:")
                print(f"            • Known Since: {profile.summary.known_since.strftime('%Y-%m-%d') if profile.summary.known_since else 'N/A'}")
                print(f"            • History Depth: {profile.summary.history_depth} days")
                print(f"            • Total Facts: {profile.summary.facts}")
                print(f"            • Avg Confidence: {profile.summary.confidence:.1f}%")
                
                print("         Categories:")
                for cat_name in ['presence', 'usage', 'behaviour', 'mobility']:
                    cat_data = getattr(profile.categories, cat_name, {})
                    count = cat_data.get('facts_count', 0) if isinstance(cat_data, dict) else 0
                    if count > 0:
                        print(f"            • {cat_name.capitalize()}: {count} facts")
                
                print("         Coverage:")
                print(f"            • Knowledge: {profile.coverage.knowledge:.1f}%")
                print(f"            • Fact: {profile.coverage.fact:.1f}%")
                
                print("         Capabilities Available:")
                available_caps = [cap for cap, is_avail in profile.capabilities.items() if is_avail]
                print(f"            • {', '.join(available_caps) if available_caps else 'None'}")
                
                # 4. Демонстрация Fluent Query API
                print("         Query API Demo:")
                q1_count = profile.query().count()
                print(f"            • profile.query().count() = {q1_count} facts")
                
                high_conf_count = profile.query().confidence(50.0).count()
                print(f"            • profile.query().confidence(50.0).count() = {high_conf_count} facts")
                
                presence_facts = profile.query().category("presence").all()
                print(f"            • profile.query().category('presence').all() = {len(presence_facts)} facts")
                
                # 5. Демонстрация ExplainService
                explain_service = ExplainService(knowledge_service)
                explain_graph = explain_service.build(profile)
                print("         Explain Graph:")
                print(f"            • Facts Traced: {explain_graph.facts_count}")
                print(f"            • Engines Involved: {', '.join(explain_graph.engines)}")
                print(f"            • Overall Confidence Trace: {explain_graph.confidence_trace.get('overall', 0):.1%}")
                
                # 6. v1.6.7: Change Detection Layer
                print("\n  [DIFF] Detecting Profile Changes...")
                
                # Получаем предыдущий профиль из кэша (если есть)
                previous_profile = profile_service.get(sample_device_id)
                
                if previous_profile is None:
                    print(f"      ℹ️  First run - no previous profile to compare")
                    print(f"      ✅ Current profile cached for next comparison")
                    diff = EMPTY_DIFF
                else:
                    # Сравниваем профили
                    differ = ProfileDiffer()
                    diff = differ.compare(previous_profile, profile)
                    
                    if diff is EMPTY_DIFF:
                        print(f"      ✅ No changes detected (idempotent)")
                    else:
                        print(f"      ✅ Changes detected: {diff.count()}")
                        print(f"         Diff ID: {diff.diff_id}")
                        
                        # Summary изменений
                        print("         Summary Changes:")
                        if diff.summary.facts_count.delta != 0:
                            print(f"            • Facts: {diff.summary.facts_count.old} → {diff.summary.facts_count.new} (delta={diff.summary.facts_count.delta})")
                        if diff.summary.confidence.delta != 0:
                            print(f"            • Confidence: {diff.summary.confidence.old:.1f}% → {diff.summary.confidence.new:.1f}% (delta={diff.summary.confidence.delta:.1f})")
                        
                        # Engines
                        if diff.engine_diff.added or diff.engine_diff.removed:
                            print("         Engine Changes:")
                            for eng in diff.engine_diff.added:
                                print(f"            • +{eng} (ADDED)")
                            for eng in diff.engine_diff.removed:
                                print(f"            • -{eng} (REMOVED)")
                        
                        # Capabilities
                        if diff.capability_diff.became_available or diff.capability_diff.became_unavailable:
                            print("         Capability Changes:")
                            for cap in diff.capability_diff.became_available:
                                print(f"            • +{cap} (AVAILABLE)")
                            for cap in diff.capability_diff.became_unavailable:
                                print(f"            • -{cap} (UNAVAILABLE)")
                        
                        # Примеры изменений фактов (только первые 3)
                        fact_changes = [c for c in diff.changes if c.subject == "fact"]
                        if fact_changes:
                            print(f"         Fact Changes (showing {min(3, len(fact_changes))} of {len(fact_changes)}):")
                            for change in fact_changes[:3]:
                                if change.type == ChangeType.ADDED:
                                    print(f"            • +{change.metadata['fact_id']} (ADDED)")
                                elif change.type == ChangeType.REMOVED:
                                    print(f"            • -{change.metadata['fact_id']} (REMOVED)")
                                elif change.type == ChangeType.UPDATED:
                                    fields = change.metadata.get('changed_fields', [])
                                    print(f"            • ~{change.metadata['fact_id']} (UPDATED: {', '.join(fields)})")
                    
                    print(f"      ✅ New profile cached for next comparison")

                # 7. v1.6.8: Domain Event Layer
                print("\n  [EVENTS] Generating Domain Events...")
                event_generator = EventGenerator()
                event_set = event_generator.generate(diff)
                
                if event_set is EMPTY_EVENT_SET:
                    print(f"      ℹ️  No domain events generated (EMPTY_DIFF or no matching rules)")
                else:
                    print(f"      ✅ Generated {event_set.count()} domain event(s)")
                    
                    # Выводим первые 3 события для демонстрации
                    events_to_show = list(event_set.events[:3])
                    for i, event in enumerate(events_to_show, 1):
                        print(f"         {i}. {event.event_type}")
                        print(f"            • Device: {event.device_uuid[:8]}...")
                        print(f"            • Origin: {event.origin.value}")
                        print(f"            • Payload: {dict(event.payload)}")
                        print(f"            • Trace: Diff={event.source_diff_id[:8]}... | Change={event.source_change_id[:8]}...")
                    
                    if event_set.count() > 3:
                        print(f"         ... and {event_set.count() - 3} more event(s)")
                
            except Exception as exc:
                print(f"  [PROFILE] ❌ Failed: {exc}")
                import traceback
                traceback.print_exc()

        # === Archivist Summary & Events ===
        print()
        archivist.print_summary()

        if all_events:
            print()
            print(f"  📢 Events ({len(all_events)}, {total_event_elapsed_ms:.1f} ms, persisted: {total_persisted}):")
            for event in all_events[:5]:
                severity_icon = {"INFO": "ℹ️", "WARNING": "⚠️", "CRITICAL": "🚨"}.get(event.severity.value, "•")
                print(f"      {severity_icon} [{event.severity.value}] {event.title}")
        else:
            print()
            print(f"  📢 Events: Нет изменений ({total_event_elapsed_ms:.1f} ms)")

        # === v1.5.1: Smoke-test History Service ===
        if history_service and first_device_id:
            print()
            print("  [HISTORY] Testing History Service...")
            try:
                device_history = history_service.get_device_history(first_device_id)
                print(f"      ✅ History Service is working! Device: {device_history.mac} | Snapshots: {len(device_history.snapshots)} | Observations: {len(device_history.observations)}")
            except Exception as exc:
                print(f"      ❌ History Service test failed: {exc}")

    devices = filter_devices(devices)
    devices = sort_devices(devices)
    save_state(devices)

    print()
    print_table(devices, collected_data)
    save_report(devices, collected_data)

    if db:
        if session_engine:
            session_engine.close_all_active_sessions(SessionEndReason.PROGRAM_SHUTDOWN)
        db.close()

    elapsed = time.time() - start
    print(f"  ⏱   Выполнено за {elapsed:.2f} сек.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
