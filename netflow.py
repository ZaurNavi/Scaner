#!/usr/bin/env python3
"""
Repeater Monitor
netflow.py

Чтение и агрегация NetFlow данных из nfdump.
v1.7.1a: Интеграция с Configuration Layer.
"""

from __future__ import annotations

import csv
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from configuration import ConfigurationManager, get_config_manager


def aggregate_netflow(configuration: Optional[ConfigurationManager] = None) -> dict[str, dict]:
    """
    Агрегирует NetFlow данные.
    v1.7.1a: Принимает configuration или использует глобальный менеджер.
    """
    if configuration is None:
        configuration = get_config_manager()

    # Получаем настройки из Configuration Layer
    active_window_hours = configuration.get("netflow.active_window", 5)
    nfdump_dir = Path(configuration.get("netflow.flow_directory", "/var/nfdump"))
    network_prefix = configuration.get("network.prefix", "192.168.1")
    excluded_ips_str = configuration.get("collector.detection.excluded_ips", "")
    excluded_ips = [ip.strip() for ip in excluded_ips_str.split(",") if ip.strip()]
    subprocess_timeout = configuration.get("netflow.subprocess_timeout", 60)
    min_traffic_bytes = configuration.get("netflow.min_traffic_bytes", 200)

    # 1. Поиск файлов
    if not nfdump_dir.exists():
        return {}

    cutoff = datetime.now() - timedelta(hours=active_window_hours)
    files = []

    for file in nfdump_dir.glob("nfcapd.*"):
        try:
            timestamp = datetime.strptime(file.name.replace("nfcapd.", ""), "%Y%m%d%H%M")
            if timestamp >= cutoff:
                files.append(file)
        except Exception:
            continue

    files = sorted(files)
    if not files:
        return {}

    # 2. Чтение nfdump
    cmd = ["nfdump"]
    for file in files:
        cmd.extend(["-r", str(file)])
    cmd.extend(["-o", "csv"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=subprocess_timeout)
        if result.returncode != 0:
            return {}
        rows = list(csv.reader(result.stdout.splitlines()))
    except Exception:
        return {}

    if len(rows) < 2:
        return {}

    # 3. Агрегация
    header = rows[0]
    try:
        idx_ts = header.index("ts")
        idx_td = header.index("td")
        idx_sa = header.index("sa")
        idx_da = header.index("da")
        idx_ibyt = header.index("ibyt")
        idx_obyt = header.index("obyt")
    except ValueError:
        return {}

    result_dict = {}

    for row in rows[1:]:
        try:
            sa = row[idx_sa]
            da = row[idx_da]

            if sa.startswith(network_prefix):
                ip = sa
                traffic = int(row[idx_ibyt])
            elif da.startswith(network_prefix):
                ip = da
                traffic = int(row[idx_obyt])
            else:
                continue

            if ip in excluded_ips:
                continue

            if traffic < min_traffic_bytes:
                continue

            ts = datetime.strptime(row[idx_ts], "%Y-%m-%d %H:%M:%S")
            duration = float(row[idx_td])

        except Exception:
            continue

        if ip not in result_dict:
            result_dict[ip] = {"flows": 0, "bytes": 0, "first_seen": ts, "duration": 0.0}

        result_dict[ip]["flows"] += 1
        result_dict[ip]["bytes"] += traffic
        result_dict[ip]["duration"] += duration

        if ts < result_dict[ip]["first_seen"]:
            result_dict[ip]["first_seen"] = ts

    # 4. Формирование финального результата
    final = {}
    for ip, item in result_dict.items():
        mb = item["bytes"] / 1024 / 1024
        hours = item["duration"] / 3600 if item["duration"] > 0 else (1 / 3600)

        final[ip] = {
            "flows": item["flows"],
            "bytes": item["bytes"],
            "megabytes": round(mb, 2),
            "first_seen": item["first_seen"].strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": round(item["duration"], 2),
            "hours_online": round(hours, 2),
            "mb_per_hour": round(mb / hours, 2),
        }

    return final


def main():
    print("\nRepeater Monitor")
    print("-" * 60)
    
    config = get_config_manager()
    print(f"NetFlow dir : {config.get('netflow.flow_directory')}")
    print(f"Network     : {config.get('network.prefix')}")
    print(f"Window      : {config.get('netflow.active_window')} hours")
    print()

    data = aggregate_netflow(config)
    print(f"Получено устройств: {len(data)}\n")

    devices = sorted(data.items(), key=lambda x: x[1]["mb_per_hour"], reverse=True)
    for ip, item in devices:
        print(f"{ip:15} {item['flows']:7} flows {item['megabytes']:10.2f} MB {item['mb_per_hour']:10.2f} MB/h")
    
    print("\nNetFlow модуль работает успешно.")


if __name__ == "__main__":
    main()
