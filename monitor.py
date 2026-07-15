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
from traffic import traffic_collector  # <-- v1.5.2: ДОБАВЛЕНО


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
                raw_data=traffic_info.to_dict(),
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

            # Маппим данные контроллера на IP-адреса для бесшовной интеграции с Archivist
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

            # Внедряем данные Omada в существующий collected_data
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

    # === v1.4.0 + v1.4.1: Archivist + Event Engine + Event Persister ===
    if archivist and scan:
        print()
        print("  [ARCHIVIST] Saving bundles...")

        # Инициализация Event Engine (чистый вычислитель)
        event_engine = EventEngine(Repository(db))

        # Инициализация Event Persister (слой сохранения)
        from events import EventRepository, EventPersister
        event_repo = EventRepository(db)
        event_persister = EventPersister(event_repo)

        all_events = []
        total_event_elapsed_ms = 0.0
        total_persisted = 0

        # Сохраняем device_id для smoke-test History Service
        first_device_id = None

        for device in devices:
            collected = collected_data.get(device.ip, CollectedData())
            bundle = build_snapshot_bundle(device, scan, collected)

            result = archivist.save(bundle)

            if result.success:
                print(f"      💾 Saved bundle: {device.ip} ({result.observations_saved} obs, {result.evidence_saved} ev)")
                print(f"      [DEBUG] result.device_id = '{result.device_id}'")
                
                # Сохраняем device_id первого устройства для smoke-test
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
                
                snapshots_count = len(device_history.snapshots)
                observations_count = len(device_history.observations)
                events_count = len(device_history.events)
                
                ip_history = history_service.get_ip_history(first_device_id)
                unique_ips = len(set(entry["ip"] for entry in ip_history))
                
                hostname_history = history_service.get_hostname_history(first_device_id)
                unique_hostnames = len(set(entry["hostname"] for entry in hostname_history))
                
                print(f"      ✅ History Service is working!")
                print(f"         Device: {device_history.mac}")
                print(f"         First seen: {device_history.first_seen.strftime('%Y-%m-%d %H:%M')}")
                print(f"         Last seen: {device_history.last_seen.strftime('%Y-%m-%d %H:%M')}")
                print(f"         Snapshots: {snapshots_count}")
                print(f"         Observations: {observations_count}")
                print(f"         Events: {events_count}")
                print(f"         Unique IPs: {unique_ips}")
                print(f"         Unique Hostnames: {unique_hostnames}")
                
                if ip_history:
                    recent_ips = ip_history[-3:]
                    ip_list = ", ".join([f"{entry['ip']} ({entry['timestamp'].strftime('%H:%M')})" for entry in recent_ips])
                    print(f"         Recent IPs: {ip_list}")
                
            except Exception as exc:
                print(f"      ❌ History Service test failed: {exc}")
        # ===========================================

    devices = filter_devices(devices)
    devices = sort_devices(devices)
    save_state(devices)

    print()
    print_table(devices, collected_data)
    save_report(devices, collected_data)

    if db:
        db.close()

    elapsed = time.time() - start
    print(f"  ⏱   Выполнено за {elapsed:.2f} сек.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
