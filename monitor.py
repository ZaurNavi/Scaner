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
from mobility.registry import ProviderRegistry as MobilityProviderRegistry  # <-- v1.5.7
from mobility.providers.session_provider import SessionMetricsProvider
from mobility.features.roaming_feature import build_roaming_rate

# v1.6.1: Presence Engine импорты
from presence import PresenceService
from presence.registry import ProviderRegistry as PresenceProviderRegistry
from presence.providers.history_provider import HistoryProvider
from presence.features.visit_feature import build_history_depth_days  # Триггерит @register_feature


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


def main() -> int:
    start = time.time()
    print_header()

    archivist, db, scan = init_archivist()
    
    # === v1.5.1: Инициализация History Service ===
    history_service = None
    if db:
        try:
            history_service = HistoryService(db.get_connection())
            print("  [HISTORY] ✅ History Service initialized")
        except Exception as exc:
            print(f"  [HISTORY] ❌ History Service initialization failed: {exc}")
    # ===============================================

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
    # ==============================================================================

    devices = fingerprint_all(devices, collected_data)
    
    # === v1.5.0: Обогащение метаданных устройств из коллекторов ===
    enrich_device_metadata(devices, collected_data)
    # ===============================================================
    
    analyze_all(devices)

    save_debug_json(devices, collected_data)

    # === v1.4.0 + v1.4.1 + v1.5.3 + v1.5.4 + v1.5.5 + v1.5.6 + v1.5.7 + v1.6.1: Archivist + Event + Session + Identity + Confidence + Behaviour + Mobility + Presence ===
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

        # === v1.5.3: Session Engine Processing ===
        session_engine = None
        if history_service and db:
            try:
                session_engine = SessionEngine(history_service, Repository(db))
                print("\n  [SESSION] ✅ Session Engine initialized (with Recovery)")
                
                print("  [SESSION] Processing new snapshots...")
                for ip, device_id in ip_to_device_id.items():
                    snapshots = history_service.get_snapshots(device_id)
                    if snapshots:
                        snap_dicts = [
                            {
                                "timestamp": s.timestamp.isoformat(),
                                "ip": s.ip,
                                "hostname": s.hostname
                            } for s in snapshots
                        ]
                        session_engine.process_snapshots(device_id, snap_dicts)
                
                if first_device_id:
                    active_sess = session_engine.get_active_session(first_device_id)
                    if active_sess:
                        print(f"      ✅ Active Session for {first_device_id[:8]}...")
                        print(f"         Duration: {active_sess.duration or 0:.0f}s")
                        print(f"         Snapshots: {active_sess.snapshots_count}")
                    else:
                        print("      ℹ️ No active session (device might be in timeout).")
            except Exception as exc:
                print(f"  [SESSION] ❌ Initialization/Processing failed: {exc}")
        # ===========================================

        # === v1.5.4: Identity Engine Processing ===
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
                    print(f"      Sample Identity:")
                    print(f"         Device: {sample.device_id[:8]}...")
                    print(f"         MAC: {sample.primary_mac}")
                    print(f"         Known IPs: {len(sample.network.known_ips)}")
                    print(f"         Known Hostnames: {len(sample.device.known_hostnames)}")
                    print(f"         Known APs: {len(sample.network.known_aps)}")
                    print(f"         Known SSIDs: {len(sample.network.known_ssids)}")
            except Exception as exc:
                print(f"  [IDENTITY] ❌ Failed: {exc}")
                import traceback
                traceback.print_exc()
        # ===========================================

        # === v1.5.5: Confidence Service ===
        confidence_service = None
        if identity_service and profiles:
            try:
                confidence_service = ConfidenceService(identity_service)
                print("\n  [CONFIDENCE] Evaluating confidence...")
                
                sample_device_id = profiles[0].device_id
                confidence_profile = confidence_service.get_profile(sample_device_id)
                
                if confidence_profile:
                    print(f"      ✅ Confidence Profile for {sample_device_id[:8]}...")
                    print(f"         Coverage: {confidence_profile.coverage:.1f}%")
                    print(f"         Total Facts: {confidence_profile.statistics.total_facts}")
                    print(f"         Evaluated: {confidence_profile.statistics.evaluated}")
                    
                    if confidence_profile.summary.vendor:
                        print(f"         Best Vendor: {confidence_profile.summary.vendor.value} ({confidence_profile.summary.vendor.confidence:.1f}%)")
                    if confidence_profile.summary.os:
                        print(f"         Best OS: {confidence_profile.summary.os.value} ({confidence_profile.summary.os.confidence:.1f}%)")
                    if confidence_profile.summary.hostname:
                        print(f"         Best Hostname: {confidence_profile.summary.hostname.value} ({confidence_profile.summary.hostname.confidence:.1f}%)")
                    
                    vendor_explain = confidence_service.explain(sample_device_id, FactCategory.VENDOR)
                    if vendor_explain:
                        print(f"         Vendor Explanation:")
                        print(f"            Value: {vendor_explain['value']}")
                        print(f"            Confidence: {vendor_explain['confidence']:.1f}%")
                        print(f"            Raw Score: {vendor_explain['raw_score']}")
                        print(f"            Reasons: {', '.join(vendor_explain['reasons'])}")
                    
                    vendor_ranked = confidence_service.get_ranked(sample_device_id, FactCategory.VENDOR)
                    if vendor_ranked and len(vendor_ranked) > 1:
                        print(f"         Vendor Alternatives:")
                        for i, alt in enumerate(vendor_ranked[:3], 1):
                            print(f"            {i}. {alt.value}: {alt.confidence:.1f}%")
            except Exception as exc:
                print(f"  [CONFIDENCE] ❌ Failed: {exc}")
                import traceback
                traceback.print_exc()
        # ===========================================

        # === v1.5.6: Behaviour Engine ===
        behaviour_service = None
        if identity_service and profiles:
            try:
                behaviour_service = BehaviourService(
                    history_service,
                    identity_service,
                    session_engine
                )
                print("\n  [BEHAVIOUR] Analyzing behaviour...")
                
                sample_device_id = profiles[0].device_id
                behaviour_profile = behaviour_service.get_profile(sample_device_id)
                
                if behaviour_profile:
                    print(f"      ✅ Behaviour Profile for {sample_device_id[:8]}...")
                    print(f"         Feature Coverage: {behaviour_profile.feature_coverage:.1f}%")
                    print(f"         Behaviour Coverage: {behaviour_profile.behaviour_coverage:.1f}%")
                    print(f"         Total Facts: {behaviour_profile.summary.facts_total}")
                    print(f"         High Confidence: {behaviour_profile.summary.high}")
                    
                    if behaviour_profile.facts:
                        print(f"         Detected Behaviours:")
                        for fact in behaviour_profile.facts[:5]:
                            print(f"            • {fact.category.value}: {fact.measured_value} (threshold: {fact.threshold}) → {fact.confidence:.1f}% [{fact.rule_id}]")
                    
                    if behaviour_profile.facts:
                        first_fact = behaviour_profile.facts[0]
                        explain = behaviour_service.explain(sample_device_id, first_fact.category)
                        if explain:
                            print(f"         Explanation for {explain['category']}:")
                            print(f"            Feature: {explain['feature']}")
                            print(f"            Measured: {explain['measured_value']}")
                            print(f"            Threshold: {explain['threshold']}")
                            print(f"            Rule ID: {explain['rule_id']}")
                            print(f"            Confidence: {explain['confidence']:.1f}%")
                            print(f"            Status: {explain['status']}")
            except Exception as exc:
                print(f"  [BEHAVIOUR] ❌ Failed: {exc}")
                import traceback
                traceback.print_exc()
        # ===========================================

        # === v1.5.7: Mobility Engine ===
        mobility_service = None
        if behaviour_service and session_engine and history_service:
            try:
                # Регистрация провайдеров (Open/Closed Principle)
                MobilityProviderRegistry.register("session_provider", SessionMetricsProvider)
                
                mobility_service = MobilityService(
                    behaviour_service=behaviour_service,
                    session_engine=session_engine,
                    history_service=history_service
                )
                print("\n  [MOBILITY] Analyzing movement patterns...")
                
                sample_device_id = profiles[0].device_id
                mobility_profile = mobility_service.get_profile(sample_device_id)
                debug_info = mobility_service.debug(sample_device_id)
                
                if mobility_profile:
                    print(f"      ✅ Mobility Profile for {sample_device_id[:8]}...")
                    print(f"         Feature Coverage: {mobility_profile.feature_coverage:.1f}% (Available/Supported)")
                    print(f"         Mobility Coverage: {mobility_profile.mobility_coverage:.1f}% (Matched/Enabled Rules)")
                    print(f"         Facts Detected: {len(mobility_profile.facts)}")
                    
                    if mobility_profile.facts:
                        print(f"         Detected Mobility Patterns:")
                        for fact in mobility_profile.facts:
                            print(f"            • {fact.category.value}: {fact.measured_value} (Score: {fact.score}, Rule: {', '.join(fact.matched_rules)})")
                    
                    if debug_info:
                        print(f"         Debug:")
                        print(f"            Computation Time: {debug_info.computation_time_ms:.2f}ms")
                        if debug_info.provider_times:
                            print(f"            Provider Times:")
                            for provider, time_ms in debug_info.provider_times.items():
                                print(f"               • {provider}: {time_ms:.2f}ms")
                        if debug_info.feature_times:
                            print(f"            Feature Builder Times:")
                            for feature, time_ms in list(debug_info.feature_times.items())[:3]:
                                print(f"               • {feature}: {time_ms:.2f}ms")
                        if debug_info.skipped_rules:
                            print(f"            Skipped Rules:")
                            for rule in debug_info.skipped_rules[:2]:
                                print(f"               • {rule}")
                        if debug_info.missing_features:
                            print(f"            Missing Features: {', '.join(debug_info.missing_features)}")
                            
            except Exception as exc:
                print(f"  [MOBILITY] ❌ Failed: {exc}")
                import traceback
                traceback.print_exc()
        # ===========================================

        # === v1.6.1: Presence Engine ===
        presence_service = None
        if history_service and profiles:
            try:
                # Регистрация провайдеров через PresenceProviderRegistry (Замечание №3: с version)
                PresenceProviderRegistry.register(
                    "history_provider", 
                    HistoryProvider, 
                    version="1.0.0",
                    priority=10,
                    dependencies=[]
                )
                
                presence_service = PresenceService(history_service)
                print("\n  [PRESENCE] Analyzing temporal presence...")
                
                sample_device_id = profiles[0].device_id
                presence_profile = presence_service.get_profile(sample_device_id)
                debug_info = presence_service.debug(sample_device_id)
                
                if presence_profile:
                    print(f"      ✅ Presence Profile for {sample_device_id[:8]}...")
                    print(f"         Metric Coverage: {presence_profile.metric_coverage:.1f}%")
                    print(f"         Feature Coverage: {presence_profile.feature_coverage:.1f}%")
                    print(f"         Rule Match Ratio: {presence_profile.rule_match_ratio:.1f}%")  # Замечание №5
                    print(f"         Facts Detected: {len(presence_profile.facts)}")
                    print(f"         Timeline Events: {len(presence_profile.timeline.events)}")
                    
                    # Показываем Presence Patterns
                    if presence_profile.facts:
                        print(f"         Presence Patterns:")
                        for fact in presence_profile.facts:
                            print(f"            • {fact.category.value}: {fact.measured_value} (Score: {fact.score}, Rule: {', '.join(fact.matched_rules)})")
                    
                    # Показываем Execution Order (Замечание №10)
                    if debug_info:
                        print(f"         Debug:")
                        print(f"            Computation Time: {debug_info.computation_time_ms:.2f}ms")
                        print(f"            Cache Hit: {debug_info.cache_hit}")  # Замечание №14
                        print(f"            Cache Key: {debug_info.cache_key}")  # Замечание №14
                        print(f"            Engine Version: {debug_info.engine_version}")  # Замечание №14
                        print(f"            Feature Version: {debug_info.feature_version}")  # Замечание №14
                        print(f"            Provider Version: {debug_info.provider_version}")  # Замечание №14
                        
                        if debug_info.provider_times:
                            print(f"            Provider Times:")
                            for provider, time_ms in debug_info.provider_times.items():
                                print(f"               • {provider}: {time_ms:.2f}ms")
                        if debug_info.builder_times:  # Замечание №12
                            print(f"            Builder Times:")
                            for builder, time_ms in debug_info.builder_times.items():
                                print(f"               • {builder}: {time_ms:.2f}ms")
                        if debug_info.feature_times:
                            print(f"            Feature Builder Times:")
                            for feature, time_ms in list(debug_info.feature_times.items())[:3]:
                                print(f"               • {feature}: {time_ms:.2f}ms")
                        if debug_info.skipped_rules:
                            print(f"            Skipped Rules:")
                            for rule in debug_info.skipped_rules[:2]:
                                print(f"               • {rule}")
                        if debug_info.missing_features:
                            print(f"            Missing Features: {', '.join(debug_info.missing_features)}")
                            
            except Exception as exc:
                print(f"  [PRESENCE] ❌ Failed: {exc}")
                import traceback
                traceback.print_exc()
        # ===========================================

        print()
        archivist.print_summary()

        if all_events:
            print()
            print(f"  📢 Events ({len(all_events)}, {total_event_elapsed_ms:.1f} ms, persisted: {total_persisted}):")
            for event in all_events:
                severity_icon = {"INFO": "ℹ️", "WARNING": "⚠️", "CRITICAL": "🚨"}.get(event.severity.value, "•")
                print(f"      {severity_icon} [{event.severity.value}] {event.title}")
                if event.old_value and event.new_value:
                    print(f"         {event.old_value} → {event.new_value}")
                else:
                    print(f"         {event.description}")
        else:
            print()
            print(f"  📢 Events: Нет изменений (состояние устройств не изменилось, {total_event_elapsed_ms:.1f} ms)")

        # === v1.5.1: Smoke-test History Service ===
        if history_service and first_device_id:
            print()
            print("  [HISTORY] Testing History Service...")
            try:
                device_history = history_service.get_device_history(first_device_id)
                print(f"      ✅ History Service is working!")
                print(f"         Device: {device_history.mac}")
                print(f"         Snapshots: {len(device_history.snapshots)}")
                print(f"         Observations: {len(device_history.observations)}")
            except Exception as exc:
                print(f"      ❌ History Service test failed: {exc}")

    devices = filter_devices(devices)
    devices = sort_devices(devices)
    save_state(devices)

    print()
    print_table(devices, collected_data)
    save_report(devices, collected_data)

    if db:
        # === v1.5.3: Корректное закрытие сессий перед выходом ===
        if session_engine:
            session_engine.close_all_active_sessions(SessionEndReason.PROGRAM_SHUTDOWN)
        db.close()

    elapsed = time.time() - start
    print(f"  ⏱   Выполнено за {elapsed:.2f} сек.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
