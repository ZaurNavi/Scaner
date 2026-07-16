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

# v1.6.3: Scanner Platform Core импорты
from scanner_platform import Pipeline, PlatformValidator, VersionSnapshot, DeviceState


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
    """
    Безопасное извлечение значения фичи из разных типов контейнеров:
    - dict (Mobility, Presence, Usage)
    - dataclass FeatureSet (Behaviour)
    """
    if not features:
        return None
    
    # Словарь (Mobility, Presence, Usage)
    if isinstance(features, dict):
        feature = features.get(feature_id)
        if feature and hasattr(feature, 'value'):
            return feature
        return feature
    
    # FeatureSet как dataclass (Behaviour)
    if hasattr(features, feature_id):
        value = getattr(features, feature_id)
        if value is not None:
            # Возвращаем как объект с name/value/unit
            return type('FeatureWrapper', (), {
                'name': feature_id,
                'value': value,
                'unit': _get_unit_for_feature(feature_id)
            })()
    
    return None


def _get_unit_for_feature(feature_id: str) -> str:
    """Возвращает единицу измерения для известных фич Behaviour."""
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
    }
    return units.get(feature_id, '')


def _safe_get_metric_value(metrics, metric_id):
    """Безопасное извлечение значения метрики из разных типов контейнеров."""
    if not metrics:
        return 0
    
    # PresenceMetricSet/UsageMetricSet (dataclass с полем metrics)
    if hasattr(metrics, 'metrics') and isinstance(metrics.metrics, dict):
        metric = metrics.metrics.get(metric_id)
        if metric and hasattr(metric, 'value'):
            return metric.value
    
    # Обычный dict
    if isinstance(metrics, dict):
        metric = metrics.get(metric_id)
        if metric:
            if hasattr(metric, 'value'):
                return metric.value
            return metric
    
    return 0


def _format_engine_output(engine_name: str, profile, debug_info, engine_type: str = "generic"):
    """
    Единый форматтер вывода для всех аналитических движков.
    Работает с унифицированными моделями Behaviour, Mobility, Presence и Usage.
    """
    print(f"\n  [{engine_name}] Analyzing {engine_type}...")
    if not profile:
        print(f"      ❌ {engine_name} Profile not generated.")
        return

    identity_id = _safe_get(profile, 'identity_id', 'unknown')
    print(f"      ✅ {engine_name} Profile for {identity_id[:8]}...")
    
    # 1. Coverage
    print("         Coverage:")
    metric_coverage = _safe_get(profile, 'metric_coverage')
    if metric_coverage is not None:
        print(f"            • Metric Coverage: {metric_coverage:.1f}%")
    
    feature_coverage = _safe_get(profile, 'feature_coverage', 0.0)
    print(f"            • Feature Coverage: {feature_coverage:.1f}%")
    
    ratio_name = "Rule Match Ratio" if hasattr(profile, 'rule_match_ratio') else "Engine Coverage"
    ratio_val = _safe_get(profile, 'rule_match_ratio', feature_coverage)
    print(f"            • {ratio_name}: {ratio_val:.1f}%")

    # 2. Timeline (есть в Mobility, Presence и Usage)
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

    # 3. Detected Facts
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

    # Explain Summary
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

    # 4. Performance & Debug
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


def main() -> int:
    start = time.time()
    print_header()

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

    # === v1.4.0 + v1.4.1 + v1.5.3 + v1.5.4 + v1.5.5 + v1.5.6 + v1.5.7 + v1.6.1 + v1.6.2 + v1.6.3 ===
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

        # === v1.5.5: Confidence Service ===
        if identity_service and profiles:
            try:
                confidence_service = ConfidenceService(identity_service)
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

        # === v1.5.6: Behaviour Engine ===
        behaviour_service = None
        if identity_service and profiles:
            try:
                behaviour_service = BehaviourService(history_service, identity_service, session_engine)
                sample_device_id = profiles[0].device_id
                bp = behaviour_service.get_profile(sample_device_id)
                bd = behaviour_service.debug(sample_device_id) if hasattr(behaviour_service, 'debug') else None
                _format_engine_output("BEHAVIOUR", bp, bd, engine_type="behavioural patterns")
            except Exception as exc:
                print(f"  [BEHAVIOUR] ❌ Failed: {exc}")

        # === v1.5.7: Mobility Engine ===
        mobility_service = None
        if behaviour_service and session_engine and history_service:
            try:
                MobilityProviderRegistry.register("session_provider", SessionMetricsProvider)
                mobility_service = MobilityService(behaviour_service, session_engine, history_service)
                sample_device_id = profiles[0].device_id
                mp = mobility_service.get_profile(sample_device_id)
                md = mobility_service.debug(sample_device_id) if hasattr(mobility_service, 'debug') else None
                _format_engine_output("MOBILITY", mp, md, engine_type="movement patterns")
            except Exception as exc:
                print(f"  [MOBILITY] ❌ Failed: {exc}")

        # === v1.6.1: Presence Engine ===
        presence_service = None
        if history_service and profiles:
            try:
                PresenceProviderRegistry.register("history_provider", HistoryProvider, version="1.0.0", priority=10, dependencies=[])
                presence_service = PresenceService(history_service)
                sample_device_id = profiles[0].device_id
                pp = presence_service.get_profile(sample_device_id)
                pd = presence_service.debug(sample_device_id) if hasattr(presence_service, 'debug') else None
                _format_engine_output("PRESENCE", pp, pd, engine_type="temporal presence")
            except Exception as exc:
                print(f"  [PRESENCE] ❌ Failed: {exc}")

        # === v1.6.2: Usage Engine ===
        usage_service = None
        if history_service and profiles:
            try:
                UsageProviderRegistry.register("traffic_provider", TrafficProvider, version="1.0.0", priority=10, dependencies=[])
                usage_service = UsageService(history_service)
                sample_device_id = profiles[0].device_id
                up = usage_service.get_profile(sample_device_id)
                ud = usage_service.debug(sample_device_id) if hasattr(usage_service, 'debug') else None
                _format_engine_output("USAGE", up, ud, engine_type="network usage patterns")
            except Exception as exc:
                print(f"  [USAGE] ❌ Failed: {exc}")
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
