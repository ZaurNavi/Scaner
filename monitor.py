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
)
from fingerprint.analysis import fingerprint_all
from fingerprint.collectors.base import collect_all, CollectedData
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

    devices = fingerprint_all(devices, collected_data)
    analyze_all(devices)

    save_debug_json(devices, collected_data)

    # === v1.4.0: Archivist + Event Engine ===
    if archivist and scan:
        print()
        print("  [ARCHIVIST] Saving bundles...")
        
        event_engine = EventEngine(Repository(db))
        
        all_events = []
        total_event_elapsed_ms = 0.0
        
        for device in devices:
            collected = collected_data.get(device.ip, CollectedData())
            bundle = build_snapshot_bundle(device, scan, collected)
            
            result = archivist.save(bundle)
            
            if result.success:
                print(f"      💾 Saved bundle: {device.ip} ({result.observations_saved} obs, {result.evidence_saved} ev)")
                
                # === ОТЛАДКА: проверяем, какой device_id мы передаём ===
                print(f"      [DEBUG] result.device_id = '{result.device_id}'")
                
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
            else:
                print(f"      ❌ Failed: {device.ip} — {result.error_message}")

        print()
        archivist.print_summary()
        
        if all_events:
            print()
            print(f"  📢 Events ({len(all_events)}, {total_event_elapsed_ms:.1f} ms):")
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
