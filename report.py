#!/usr/bin/env python3
"""
Repeater Monitor
report.py

Построение отчётов: объединение SNMP + NetFlow + Vendor,
определение статуса устройства, вывод таблицы, сохранение в файлы.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from config import App, Detection, Export, Paths, Thresholds
from constants import (
    CSV_ENCODING,
    CSV_SEPARATOR,
    DATE_FORMAT,
    REPORT_CSV,
    REPORT_JSON,
    REPORT_TXT,
    STATUS_NORMAL,
    STATUS_SUSPECT,
    STATUS_WARNING,
    SUSPECT_VENDOR_KEYWORDS,
    TABLE_WIDTH,
)
from models import Device
from vendors import get_vendor
from fingerprint.vendor_normalizer import normalize_vendor  # <-- ДОБАВЛЕНО
from fingerprint import fingerprint_all
from fingerprint.collectors.base import CollectedData
from fingerprint.correlation import engine as correlation_engine


# ---------------------------------------------------------
# Константы форматирования
# ---------------------------------------------------------

MAX_VENDOR_WIDTH = 18


# ---------------------------------------------------------
# Сборка устройств
# ---------------------------------------------------------


def _empty_flow() -> dict:
    """
    Пустые данные NetFlow для устройства,
    которое не было замечено в трафике.
    """
    return {
        "flows": 0,
        "bytes": 0,
        "megabytes": 0.0,
        "first_seen": "",
        "duration_seconds": 0.0,
        "hours_online": 0.0,
        "mb_per_hour": 0.0,
    }


def build_devices(
    arp: dict[str, str],
    netflow: dict[str, dict],
) -> list[Device]:
    """
    Объединяет данные SNMP и NetFlow в список Device.
    """
    devices = []

    for ip, mac in arp.items():
        if ip in Detection.EXCLUDED_IPS:
            continue

        if Detection.REQUIRE_MAC and not mac:
            continue

        flow = netflow.get(ip) or _empty_flow()

        device = Device(
            ip=ip,
            mac=mac,
            vendor=normalize_vendor(get_vendor(mac)),  # <-- ИЗМЕНЕНО: добавлена нормализация
            flows=flow["flows"],
            bytes=flow["bytes"],
            megabytes=flow["megabytes"],
            first_seen=flow["first_seen"],
            duration_seconds=flow["duration_seconds"],
            hours_online=flow["hours_online"],
            mb_per_hour=flow["mb_per_hour"],
        )

        devices.append(device)

    return devices


# ---------------------------------------------------------
# Детекция подозрительных производителей
# ---------------------------------------------------------


def detect_vendor(device: Device) -> bool:
    vendor_lower = device.vendor.lower()
    if any(sv in vendor_lower for sv in SUSPECT_VENDOR_KEYWORDS):
        device.status = STATUS_SUSPECT
        device.reason = f"Производитель: {device.vendor}"
        return True
    return False


# ---------------------------------------------------------
# Детекция аномалии flows
# ---------------------------------------------------------


def detect_flow_anomaly(device: Device) -> bool:
    if device.flows > Thresholds.SUSPECT_FLOWS_THRESHOLD and device.mb_per_hour < Thresholds.LOW_MB_PER_HOUR:
        device.status = STATUS_SUSPECT
        device.reason = f"Много flows ({device.flows}) при низком трафике"
        return True

    if device.flows > Thresholds.HIGH_FLOWS_THRESHOLD:
        device.status = STATUS_SUSPECT
        device.reason = f"Аномально много flows: {device.flows}"
        return True

    return False


# ---------------------------------------------------------
# Детекция фонового устройства
# ---------------------------------------------------------


def detect_background_device(device: Device) -> bool:
    if (
        device.hours_online >= Thresholds.MIN_ONLINE_MINUTES / 60
        and device.megabytes < Thresholds.MIN_TOTAL_MB
    ):
        device.status = STATUS_WARNING
        device.reason = "Фоновое устройство (низкий трафик)"
        return True
    return False


# ---------------------------------------------------------
# Детекция высокого трафика
# ---------------------------------------------------------


def detect_high_traffic(device: Device) -> bool:
    if device.mb_per_hour > Thresholds.NORMAL_MB_PER_HOUR:
        device.status = STATUS_WARNING
        device.reason = f"Высокий трафик: {device.mb_per_hour:.1f} MB/h"
        return True
    return False


# ---------------------------------------------------------
# Анализ устройства
# ---------------------------------------------------------


def analyze(device: Device) -> None:
    if detect_vendor(device):
        return
    if detect_flow_anomaly(device):
        return
    if detect_background_device(device):
        return
    if detect_high_traffic(device):
        return

    device.status = STATUS_NORMAL
    device.reason = "—"


def analyze_all(devices: list[Device]) -> list[Device]:
    for device in devices:
        analyze(device)
    return devices


# ---------------------------------------------------------
# Сортировка и фильтрация
# ---------------------------------------------------------


def sort_devices(devices: list[Device]) -> list[Device]:
    if Detection.SORT_SUSPECTS_FIRST:
        def sort_key(d: Device):
            priority = 0 if d.status == STATUS_SUSPECT else 1
            return (priority, -d.mb_per_hour)
        return sorted(devices, key=sort_key)
    return sorted(devices, key=lambda d: -d.mb_per_hour)


def filter_devices(devices: list[Device]) -> list[Device]:
    if Detection.ACTIVE_ONLY:
        devices = [d for d in devices if d.flows > 0]
    return devices


# ---------------------------------------------------------
# Статистика
# ---------------------------------------------------------


def calculate_statistics(devices: list[Device]) -> dict:
    return {
        "total": len(devices),
        "suspects": sum(1 for d in devices if d.status == STATUS_SUSPECT),
        "warnings": sum(1 for d in devices if d.status == STATUS_WARNING),
        "normal": sum(1 for d in devices if d.status == STATUS_NORMAL),
    }


# ---------------------------------------------------------
# Рендер таблицы (компактный режим)
# ---------------------------------------------------------


def render_table_compact(devices: list[Device]) -> list[str]:
    lines = []
    if not devices:
        lines.append("Нет устройств для отображения.")
        return lines

    header = (
        f"{'Статус':<20}"
        f"{'IP':<16}"
        f"{'MAC':<20}"
        f"{'Vendor':<{MAX_VENDOR_WIDTH + 2}}"
        f"{'Flows':>7}"
        f"{'MB':>8}"
        f"{'MB/h':>8}"
        f"{'Часы':>7}"
        f"  Причина"
    )
    lines.append(header)
    lines.append("-" * TABLE_WIDTH)

    for d in devices:
        line = (
            f"{d.status:<20}"
            f"{d.ip:<16}"
            f"{d.mac:<20}"
            f"{d.vendor[:MAX_VENDOR_WIDTH]:<{MAX_VENDOR_WIDTH + 2}}"
            f"{d.flows:>7}"
            f"{d.megabytes:>8.2f}"
            f"{d.mb_per_hour:>8.2f}"
            f"{d.hours_online:>7.1f}"
            f"  {d.reason}"
        )
        lines.append(line)

    lines.append("-" * TABLE_WIDTH)
    stats = calculate_statistics(devices)
    lines.append(
        f"Всего: {stats['total']} | "
        f"🔴 Подозрительных: {stats['suspects']} | "
        f"🟡 Неопределённых: {stats['warnings']} | "
        f"🟢 Нормальных: {stats['normal']}"
    )
    return lines


# ---------------------------------------------------------
# Рендер таблицы (расширенный режим VERBOSE)
# ---------------------------------------------------------


def render_table_verbose(devices: list[Device]) -> list[str]:
    lines = []
    if not devices:
        lines.append("Нет устройств для отображения.")
        return lines

    header = (
        f"{'Статус':<20}"
        f"{'IP':<16}"
        f"{'MAC':<20}"
        f"{'Vendor':<20}"
        f"{'Hostname':<18}"
        f"{'Model':<16}"
        f"{'OS':<12}"
        f"{'Type':<15}"
        f"{'Conf':>4}"
        f"{'Flows':>7}"
        f"{'MB/h':>8}"
        f"  Причина"
    )
    actual_width = len(header)

    lines.append(header)
    lines.append("-" * actual_width)

    for d in devices:
        vendor = d.vendor[:18] + ".." if len(d.vendor) > 20 else d.vendor
        hostname = d.hostname[:16] + ".." if len(d.hostname) > 18 else d.hostname
        model = d.model[:14] + ".." if len(d.model) > 16 else d.model
        os_val = d.os[:10] + ".." if len(d.os) > 12 else d.os
        dev_type = d.device_type[:13] + ".." if len(d.device_type) > 15 else d.device_type

        line = (
            f"{d.status:<20}"
            f"{d.ip:<16}"
            f"{d.mac:<20}"
            f"{vendor:<20}"
            f"{hostname:<18}"
            f"{model:<16}"
            f"{os_val:<12}"
            f"{dev_type:<15}"
            f"{d.confidence:>4}"
            f"{d.flows:>7}"
            f"{d.mb_per_hour:>8.2f}"
            f"  {d.reason}"
        )
        lines.append(line)

    lines.append("-" * actual_width)
    stats = calculate_statistics(devices)
    lines.append(
        f"Всего: {stats['total']} | "
        f"🔴 Подозрительных: {stats['suspects']} | "
        f"🟡 Неопределённых: {stats['warnings']} | "
        f"🟢 Нормальных: {stats['normal']}"
    )
    return lines


# ---------------------------------------------------------
# Рендер Evidence
# ---------------------------------------------------------


def render_evidence(devices: list[Device], collected_data: dict[str, CollectedData]) -> list[str]:
    lines = []
    for d in devices:
        collected = collected_data.get(d.ip, CollectedData())
        corr = correlation_engine.correlate(d, collected)

        if not corr.evidence_items:
            continue

        lines.append(f"  📋 {d.ip} ({d.mac}) — {d.os or 'Unknown'} {d.device_type or ''} [{d.confidence}]")
        for item in corr.evidence_items:
            if item.details:
                lines.append(f"     ✔ {item.description} ({item.details}) [+{item.contribution}]")
            else:
                lines.append(f"     ✔ {item.description} [+{item.contribution}]")
        lines.append(f"     ─── Total: {corr.breakdown.total()}")
        lines.append("")
    return lines


# ---------------------------------------------------------
# Рендер таблицы (выбор режима)
# ---------------------------------------------------------


def render_table(devices: list[Device], verbose: bool = False) -> list[str]:
    if verbose:
        return render_table_verbose(devices)
    return render_table_compact(devices)


# ---------------------------------------------------------
# Печать таблицы
# ---------------------------------------------------------


def print_table(devices: list[Device], collected_data: dict[str, CollectedData] | None = None) -> None:
    if App.VERBOSE:
        header = (
            f"{'Статус':<20}"
            f"{'IP':<16}"
            f"{'MAC':<20}"
            f"{'Vendor':<20}"
            f"{'Hostname':<18}"
            f"{'Model':<16}"
            f"{'OS':<12}"
            f"{'Type':<15}"
            f"{'Conf':>4}"
            f"{'Flows':>7}"
            f"{'MB/h':>8}"
            f"  Причина"
        )
        width = len(header)
    else:
        width = TABLE_WIDTH

    print()
    print("=" * width)
    print(f"{'Repeater Monitor':^{width}}")
    print(f"{datetime.now().strftime(DATE_FORMAT):^{width}}")
    if App.VERBOSE:
        print(f"{'[VERBOSE MODE]':^{width}}")
    print("=" * width)
    print()

    for line in render_table(devices, verbose=App.VERBOSE):
        print(line)

    if App.VERBOSE and collected_data:
        evidence_lines = render_evidence(devices, collected_data)
        if evidence_lines:
            print("  🔍 Evidence Explorer:")
            print()
            for line in evidence_lines:
                print(line)
    print()


# ---------------------------------------------------------
# Сохранение TXT
# ---------------------------------------------------------


def save_txt(devices: list[Device], collected_data: dict[str, CollectedData] | None = None) -> Path:
    report_dir = Paths.REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    file_path = report_dir / REPORT_TXT

    if App.VERBOSE:
        header = (
            f"{'Статус':<20}"
            f"{'IP':<16}"
            f"{'MAC':<20}"
            f"{'Vendor':<20}"
            f"{'Hostname':<18}"
            f"{'Model':<16}"
            f"{'OS':<12}"
            f"{'Type':<15}"
            f"{'Conf':>4}"
            f"{'Flows':>7}"
            f"{'MB/h':>8}"
            f"  Причина"
        )
        width = len(header)
    else:
        width = TABLE_WIDTH

    lines = []
    lines.append("=" * width)
    lines.append(f"{'Repeater Monitor':^{width}}")
    lines.append(f"{datetime.now().strftime(DATE_FORMAT):^{width}}")
    if App.VERBOSE:
        lines.append(f"{'[VERBOSE MODE]':^{width}}")
    lines.append("=" * width)
    lines.append("")
    lines.extend(render_table(devices, verbose=App.VERBOSE))
    lines.append("")

    if App.VERBOSE and collected_data:
        evidence_lines = render_evidence(devices, collected_data)
        if evidence_lines:
            lines.append("  🔍 Evidence Explorer:")
            lines.append("")
            lines.extend(evidence_lines)

    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path


# ---------------------------------------------------------
# Сохранение CSV
# ---------------------------------------------------------


def save_csv(devices: list[Device]) -> Path:
    report_dir = Paths.REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    file_path = report_dir / REPORT_CSV

    with file_path.open("w", encoding=CSV_ENCODING, newline="") as f:
        writer = csv.writer(f, delimiter=CSV_SEPARATOR)
        writer.writerow([
            "Статус", "IP", "MAC", "Vendor", "Hostname", "Model", "OS", "Type",
            "Confidence", "Flows", "Bytes", "MB", "First Seen", "Duration (sec)", "Hours Online", "MB/h", "Причина",
        ])
        for d in devices:
            writer.writerow([
                d.status, d.ip, d.mac, d.vendor, d.hostname, d.model, d.os, d.device_type,
                d.confidence, d.flows, d.bytes, d.megabytes, d.first_seen, d.duration_seconds, d.hours_online, d.mb_per_hour, d.reason,
            ])
    return file_path


# ---------------------------------------------------------
# Сохранение JSON
# ---------------------------------------------------------


def save_json(devices: list[Device], collected_data: dict[str, CollectedData] | None = None) -> Path:
    report_dir = Paths.REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    file_path = report_dir / REPORT_JSON

    devices_data = []
    for d in devices:
        device_dict = asdict(d)
        if collected_data:
            collected = collected_data.get(d.ip, CollectedData())
            corr = correlation_engine.correlate(d, collected)
            device_dict["evidence_items"] = [e.to_dict() for e in corr.evidence_items]
        devices_data.append(device_dict)

    data = {
        "timestamp": datetime.now().strftime(DATE_FORMAT),
        "statistics": calculate_statistics(devices),
        "devices": devices_data,
    }
    file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


# ---------------------------------------------------------
# Debug JSON
# ---------------------------------------------------------


def save_debug_json(devices: list[Device], collected_data: dict[str, CollectedData]) -> Path:
    report_dir = Paths.REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    file_path = report_dir / "debug_fingerprint.json"

    data = {
        "timestamp": datetime.now().strftime(DATE_FORMAT),
        "total_devices": len(devices),
        "devices": [],
    }

    for device in devices:
        collected = collected_data.get(device.ip, CollectedData())
        device_data = {
            "ip": device.ip, "mac": device.mac, "vendor": device.vendor,
            "hostname": device.hostname, "model": device.model, "os": device.os,
            "device_type": device.device_type, "confidence": device.confidence,
            "status": device.status, "reason": device.reason, "sources": {},
        }

        for source_name, source_result in collected.sources.items():
            device_data["sources"][source_name] = {
                "elapsed_ms": source_result.elapsed_ms,
                "confidence": source_result.confidence,
                "os": source_result.os, "model": source_result.model,
                "device_type": source_result.device_type, "reason": source_result.reason,
                "ports": source_result.ports, "ttl": source_result.ttl,
                "latency_ms": source_result.latency_ms, "raw_data": source_result.raw_data,
            }

        if collected.hostname:
            device_data["sources"]["dns"] = {"hostname": collected.hostname}

        if collected.mdns.hostname or collected.mdns.model or collected.mdns.device_type:
            device_data["sources"]["mdns"] = {
                "hostname": collected.mdns.hostname,
                "model": collected.mdns.model,
                "device_type": collected.mdns.device_type,
                "services": collected.mdns.services,
            }

        corr = correlation_engine.correlate(device, collected)
        device_data["correlation"] = {
            "matched_rules": [r.to_dict() for r in corr.matched_rules],
            "reasons": corr.reasons,
            "breakdown": corr.breakdown.to_dict(),
            "fingerprint_score": corr.fingerprint_score,
            "evidence_items": [e.to_dict() for e in corr.evidence_items],
        }
        data["devices"].append(device_data)

    file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


# ---------------------------------------------------------
# Сохранение всех форматов
# ---------------------------------------------------------


def save_report(devices: list[Device], collected_data: dict[str, CollectedData] | None = None) -> None:
    saved_paths = []
    if Export.TXT:
        saved_paths.append(("TXT", save_txt(devices, collected_data)))
    if Export.CSV:
        saved_paths.append(("CSV", save_csv(devices)))
    if Export.JSON:
        saved_paths.append(("JSON", save_json(devices, collected_data)))

    if saved_paths:
        print(f"  📄  Отчёты сохранены:")
        for fmt, path in saved_paths:
            print(f"      {fmt:<4} : {path}")
        print()


# ---------------------------------------------------------
# Главный вход
# ---------------------------------------------------------


def generate_report(arp: dict[str, str], netflow: dict[str, dict]) -> list[Device]:
    devices = build_devices(arp, netflow)
    devices = fingerprint_all(devices)
    analyze_all(devices)
    devices = filter_devices(devices)
    devices = sort_devices(devices)
    print_table(devices)
    save_report(devices)
    return devices


__all__ = [
    "build_devices", "analyze_all", "filter_devices", "sort_devices",
    "print_table", "save_report", "save_debug_json", "generate_report",
]
