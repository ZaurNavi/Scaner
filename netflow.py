#!/usr/bin/env python3
"""
Repeater Monitor

netflow.py

Чтение и агрегация NetFlow данных из nfdump.
"""

from __future__ import annotations

import csv
import subprocess

from datetime import datetime, timedelta
from pathlib import Path

from config import Detection
from config import NetFlow
from config import Network
from config import Paths


# ---------------------------------------------------------
# Поиск файлов
# ---------------------------------------------------------


def get_recent_files() -> list[Path]:
    """
    Возвращает список файлов nfdump
    за последние ACTIVE_WINDOW_HOURS.
    """

    directory = Paths.NFDUMP_DIR

    if not directory.exists():
        return []

    cutoff = datetime.now() - timedelta(
        hours=NetFlow.ACTIVE_WINDOW_HOURS
    )

    files = []

    for file in directory.glob("nfcapd.*"):

        try:

            timestamp = datetime.strptime(
                file.name.replace("nfcapd.", ""),
                "%Y%m%d%H%M",
            )

        except Exception:
            continue

        if timestamp >= cutoff:
            files.append(file)

    return sorted(files)


# ---------------------------------------------------------
# Чтение nfdump
# ---------------------------------------------------------


def export_csv(files: list[Path]) -> list[list[str]]:
    """
    Читает все найденные файлы
    через nfdump.
    """

    if not files:
        return []

    cmd = [
        "nfdump",
    ]

    for file in files:
        cmd.extend(["-r", str(file)])

    cmd.extend([
        "-o",
        "csv",
    ])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    reader = csv.reader(result.stdout.splitlines())

    return list(reader)


# ---------------------------------------------------------
# Агрегация
# ---------------------------------------------------------


def aggregate_netflow() -> dict[str, dict]:

    rows = export_csv(get_recent_files())

    if len(rows) < 2:
        return {}

    header = rows[0]

    idx_ts = header.index("ts")
    idx_td = header.index("td")

    idx_sa = header.index("sa")
    idx_da = header.index("da")

    idx_ibyt = header.index("ibyt")
    idx_obyt = header.index("obyt")

    result = {}

    prefix = Network.PREFIX

    for row in rows[1:]:

        try:

            sa = row[idx_sa]
            da = row[idx_da]

            if sa.startswith(prefix):

                ip = sa
                traffic = int(row[idx_ibyt])

            elif da.startswith(prefix):

                ip = da
                traffic = int(row[idx_obyt])

            else:
                continue

            if ip in Detection.EXCLUDED_IPS:
                continue

            #
            # шум
            #

            if traffic < 200:
                continue

            ts = datetime.strptime(
                row[idx_ts],
                "%Y-%m-%d %H:%M:%S",
            )

            duration = float(row[idx_td])

        except Exception:
            continue

        if ip not in result:

            result[ip] = {

                "flows": 0,

                "bytes": 0,

                "first_seen": ts,

                "duration": 0.0,

            }

        result[ip]["flows"] += 1
        result[ip]["bytes"] += traffic
        result[ip]["duration"] += duration

        if ts < result[ip]["first_seen"]:
            result[ip]["first_seen"] = ts

    final = {}

    for ip, item in result.items():

        mb = item["bytes"] / 1024 / 1024

        hours = item["duration"] / 3600

        if hours <= 0:
            hours = 1 / 3600

        final[ip] = {

            "flows": item["flows"],

            "bytes": item["bytes"],

            "megabytes": round(mb, 2),

            "first_seen": item["first_seen"].strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "duration_seconds": round(
                item["duration"],
                2,
            ),

            "hours_online": round(
                hours,
                2,
            ),

            "mb_per_hour": round(
                mb / hours,
                2,
            ),
        }

    return final


# ---------------------------------------------------------
# Тест
# ---------------------------------------------------------


def main():

    print()

    print("Repeater Monitor")
    print("-" * 60)

    print(f"NetFlow dir : {Paths.NFDUMP_DIR}")
    print(f"Network     : {Network.SUBNET}")
    print(f"Window      : {NetFlow.ACTIVE_WINDOW_HOURS} hours")

    print()

    data = aggregate_netflow()

    print(f"Получено устройств: {len(data)}")

    print()

    devices = sorted(
        data.items(),
        key=lambda x: x[1]["mb_per_hour"],
        reverse=True,
    )

    for ip, item in devices:

        print(
            f"{ip:15}"
            f"{item['flows']:7} flows"
            f"{item['megabytes']:10.2f} MB"
            f"{item['mb_per_hour']:10.2f} MB/h"
        )

    print()

    print("NetFlow модуль работает успешно.")


if __name__ == "__main__":
    main()
