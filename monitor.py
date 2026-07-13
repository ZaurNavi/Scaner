#!/usr/bin/env python3
"""
Repeater Monitor
monitor.py

Главный модуль-оркестратор.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime

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
from fingerprint.collectors.base import collect_all
from storage.history import enrich
from storage.device_db import save_state


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


def main() -> int:

    start = time.time()

    print_header()

    # 1. SNMP
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

    # 2. NetFlow
    print("  [2/4]  Агрегация NetFlow...")

    try:
        netflow = aggregate_netflow()
    except Exception as exc:
        print()
        print(f"  ❌  Ошибка NetFlow: {exc}")
        print()
        return 1

    print(f"         Активных IP: {len(netflow)}")

    # 3. Сборка и обогащение
    print("  [3/4]  Формирование отчёта...")

    devices = build_devices(arp, netflow)
    enrich(devices)
    
    # Сбор данных из всех коллекторов
    ips = [d.ip for d in devices]
    collected_data = collect_all(ips, devices)
    
    # Fingerprint с использованием собранных данных
    devices = fingerprint_all(devices, collected_data)
    
    analyze_all(devices)
    
    # Сохранение debug JSON для ВСЕХ устройств (до фильтрации)
    save_debug_json(devices, collected_data)
    
    devices = filter_devices(devices)
    devices = sort_devices(devices)
    save_state(devices)

    # 4. Вывод и сохранение
    print()
    print_table(devices, collected_data)
    save_report(devices, collected_data)

    elapsed = time.time() - start

    print(f"  ⏱   Выполнено за {elapsed:.2f} сек.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
