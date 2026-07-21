#!/usr/bin/env python3
"""
Repeater Monitor
report.py

ES-1.8.4: Полная миграция на UnifiedObservationBatch + интеграция Omada-данных.
Удалены зависимости от CollectedData и FingerprintResult.
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
from fingerprint.vendor_normalizer import normalize_vendor
from fingerprint import fingerprint_all, UnifiedObservationBatch
from fingerprint.normalization.models import ObservationCategory


# ---------------------------------------------------------
# Константы форматирования
# ---------------------------------------------------------

MAX_VENDOR_WIDTH = 18


# ---------------------------------------------------------
# Helper: безопасное извлечение значения из Observation/UnifiedObservation
# ---------------------------------------------------------

def _get_obs_value(obs) -> any:
    """
    ES-1.8.3: Безопасно извлекает значение из Observation или UnifiedObservation.
    UnifiedObservation имеет normalized_value, Observation — только value.
    """
    return getattr(obs, 'normalized_value', None) or obs.value


def _get_obs_confidence(obs) -> float:
    """
    ES-1.8.3: Безопасно извлекает confidence из Observation или UnifiedObservation.
    """
    return getattr(obs, 'confidence', 0.5)


# ---------------------------------------------------------
# Helper: нормализация MAC и определение ОС
# ---------------------------------------------------------

def _normalize_mac(mac: str) -> str:
    """Приводит MAC к верхнему регистру без разделителей."""
    if not mac:
        return ""
    return mac.replace(":", "").replace("-", "").upper()


def _is_mac_like(value: str, device_mac: str) -> bool:
    """
    Проверяет, является ли строка MAC-адресом устройства
    (в любом формате: с двоеточиями, дефисами или без).
    """
    if not value:
        return False
    return _normalize_mac(value) == _normalize_mac(device_mac)


def _guess_os_from_device_type(device_type: str) -> str:
    """Преобразует Omada deviceType в читаемое название ОС."""
    dt = (device_type or "").lower()
    if "android" in dt:
        return "Android"
    if "ios" in dt or "iphone" in dt or "ipad" in dt:
        return "iOS"
    if "windows" in dt:
        return "Windows"
    if "linux" in dt:
        return "Linux"
    if "macos" in dt or "mac" in dt:
        return "macOS"
    return ""


# ---------------------------------------------------------
# Observation Extractor — извлечение данных из Batch
# ---------------------------------------------------------


class ObservationExtractor:
    """
    ES-1.8.3: Извлекает данные из UnifiedObservationBatch по IP.
    Заменяет legacy CollectedData.
    """
    
    def __init__(self, batch: UnifiedObservationBatch):
        self.batch = batch
    
    def get_hostname(self, ip: str) -> str:
        """Извлекает hostname из batch для IP (только DNS)."""
        hostname_obs = self.batch.by_attribute("hostname").by_collector("dns").filter(
            lambda obs: obs.metadata.ip == ip
        ).first()
        if hostname_obs:
            return _get_obs_value(hostname_obs) or ""
        return ""
    
    def get_mdns_info(self, ip: str) -> dict:
        """Извлекает mDNS информацию из batch для IP."""
        mdns_obs = self.batch.by_attribute("model").by_collector("mdns").filter(
            lambda obs: obs.metadata.ip == ip
        ).first()
        
        if not mdns_obs:
            return {}
        
        # Извлекаем все mDNS атрибуты для этого IP
        mdns_batch = self.batch.by_collector("mdns").filter(lambda obs: obs.metadata.ip == ip)
        
        result = {}
        for obs in mdns_batch:
            value = _get_obs_value(obs)
            if obs.attribute == "hostname":
                result["hostname"] = value
            elif obs.attribute == "model":
                result["model"] = value
            elif obs.attribute == "device_type":
                result["device_type"] = value
            elif obs.attribute == "services":
                result["services"] = value
        
        return result
    
    def get_omada_info(self, ip: str) -> dict:
        """Извлекает Omada информацию из batch для IP."""
        omada_obs = self.batch.by_collector("omada").by_attribute("omada_info").filter(
            lambda obs: obs.metadata.ip == ip
        ).first()
        if omada_obs:
            return _get_obs_value(omada_obs) or {}
        return {}
    
    def get_all_sources(self, ip: str) -> dict:
        """Извлекает все источники из batch для IP."""
        sources = {}
        
        # Группируем по collector_id
        collectors = set(obs.collector_id for obs in self.batch if obs.metadata.ip == ip)
        
        for collector_id in collectors:
            collector_obs = self.batch.by_collector(collector_id).filter(
                lambda obs: obs.metadata.ip == ip
            )
            
            sources[collector_id] = {
                "observations": [
                    {
                        "attribute": obs.attribute,
                        "value": _get_obs_value(obs),
                        "confidence": _get_obs_confidence(obs),
                    }
                    for obs in collector_obs
                ]
            }
        
        return sources


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
            vendor=normalize_vendor(get_vendor(mac)),
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
# Обогащение метаданных устройств из Batch
# ---------------------------------------------------------


def enrich_device_metadata(devices: list[Device], batch: UnifiedObservationBatch) -> None:
    """
    ES-1.8.4: Заполняет пустые поля Device данными из UnifiedObservationBatch.
    Приоритет источников: DNS > mDNS > Omada.
    """
    extractor = ObservationExtractor(batch)
    
    for device in devices:
        omada_info = extractor.get_omada_info(device.ip)
        mdns_info = extractor.get_mdns_info(device.ip)
        
        # 1. Hostname: DNS > mDNS > Omada (hostName или name)
        if not device.hostname or device.hostname == "Unknown":
            hostname = extractor.get_hostname(device.ip)
            if hostname:
                device.hostname = hostname
            elif mdns_info.get("hostname"):
                device.hostname = mdns_info["hostname"]
            elif omada_info.get("hostName"):
                device.hostname = omada_info["hostName"]
            elif omada_info.get("name") and not _is_mac_like(omada_info["name"], device.mac):
                device.hostname = omada_info["name"]
        
        # 2. Model: mDNS > Omada (name, если не MAC) > hostname heuristic
        if not device.model or device.model == "Unknown":
            if mdns_info.get("model"):
                device.model = mdns_info["model"]
            elif omada_info.get("name") and not _is_mac_like(omada_info["name"], device.mac):
                device.model = omada_info["name"]
            elif device.hostname and any(
                x in device.hostname.lower()
                for x in ["redmi", "galaxy", "iphone", "ipad", "macbook", "note", "honor"]
            ):
                device.model = device.hostname

        # 3. Device Type: mDNS > Omada
        if not device.device_type or device.device_type == "Unknown":
            if mdns_info.get("device_type"):
                device.device_type = mdns_info["device_type"]
            elif omada_info.get("deviceType"):
                device.device_type = omada_info["deviceType"]

        # 4. OS: из Omada deviceType (если ещё не заполнено)
        if not device.os or device.os == "Unknown":
            guessed_os = _guess_os_from_device_type(omada_info.get("deviceType", ""))
            if guessed_os:
                device.os = guessed_os

        # 5. Vendor: Если MAC рандомизирован и OUI не сработал, пробуем угадать по имени
        if device.vendor == "Unknown":
            name_to_check = (device.hostname or "").lower()
            if "samsung" in name_to_check or "galaxy" in name_to_check:
                device.vendor = "Samsung"
            elif "xiaomi" in name_to_check or "redmi" in name_to_check:
                device.vendor = "Xiaomi"
            elif "apple" in name_to_check or "iphone" in name_to_check or "ipad" in name_to_check:
                device.vendor = "Apple"
            elif "honor" in name_to_check or "huawei" in name_to_check:
                device.vendor = "Honor/Huawei"
            elif "lenovo" in name_to_check or "thinkpad" in name_to_check:
                device.vendor = "Lenovo"


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
# Рендер Evidence (из Batch)
# ---------------------------------------------------------


def render_evidence(devices: list[Device], batch: UnifiedObservationBatch) -> list[str]:
    """
    ES-1.8.3: Рендерит evidence из UnifiedObservationBatch.
    """
    lines = []
    extractor = ObservationExtractor(batch)
    
    for d in devices:
        sources = extractor.get_all_sources(d.ip)
        
        if not sources:
            continue
        
        lines.append(f"  📋 {d.ip} ({d.mac}) — {d.os or 'Unknown'} {d.device_type or ''} [{d.confidence}]")
        
        for source_name, source_data in sources.items():
            for obs in source_data["observations"]:
                if obs["confidence"] > 0:
                    lines.append(f"     ✔ {source_name}.{obs['attribute']} = {obs['value']} [confidence: {obs['confidence']:.2f}]")
        
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


def print_table(devices: list[Device], batch: UnifiedObservationBatch | None = None) -> None:
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

    if App.VERBOSE and batch:
        evidence_lines = render_evidence(devices, batch)
        if evidence_lines:
            print("  🔍 Evidence Explorer:")
            print()
            for line in evidence_lines:
                print(line)
    print()


# ---------------------------------------------------------
# Сохранение TXT
# ---------------------------------------------------------


def save_txt(devices: list[Device], batch: UnifiedObservationBatch | None = None) -> Path:
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

    if App.VERBOSE and batch:
        evidence_lines = render_evidence(devices, batch)
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


def save_json(devices: list[Device], batch: UnifiedObservationBatch | None = None) -> Path:
    report_dir = Paths.REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    file_path = report_dir / REPORT_JSON

    extractor = ObservationExtractor(batch) if batch else None
    
    devices_data = []
    for d in devices:
        device_dict = asdict(d)
        
        if extractor:
            sources = extractor.get_all_sources(d.ip)
            device_dict["sources"] = sources
        
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


def save_debug_json(devices: list[Device], batch: UnifiedObservationBatch) -> Path:
    report_dir = Paths.REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    file_path = report_dir / "debug_fingerprint.json"

    extractor = ObservationExtractor(batch)

    data = {
        "timestamp": datetime.now().strftime(DATE_FORMAT),
        "total_devices": len(devices),
        "devices": [],
    }

    for device in devices:
        device_data = {
            "ip": device.ip, "mac": device.mac, "vendor": device.vendor,
            "hostname": device.hostname, "model": device.model, "os": device.os,
            "device_type": device.device_type, "confidence": device.confidence,
            "status": device.status, "reason": device.reason, "sources": {},
        }

        # Извлекаем все источники из batch
        sources = extractor.get_all_sources(device.ip)
        device_data["sources"] = sources

        # Извлекаем hostname и mDNS
        hostname = extractor.get_hostname(device.ip)
        if hostname:
            device_data["sources"]["dns"] = {"hostname": hostname}

        mdns_info = extractor.get_mdns_info(device.ip)
        if mdns_info:
            device_data["sources"]["mdns"] = mdns_info

        data["devices"].append(device_data)

    file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


# ---------------------------------------------------------
# Сохранение всех форматов
# ---------------------------------------------------------


def save_report(devices: list[Device], batch: UnifiedObservationBatch | None = None) -> None:
    saved_paths = []
    if Export.TXT:
        saved_paths.append(("TXT", save_txt(devices, batch)))
    if Export.CSV:
        saved_paths.append(("CSV", save_csv(devices)))
    if Export.JSON:
        saved_paths.append(("JSON", save_json(devices, batch)))

    if saved_paths:
        print(f"  📄  Отчёты сохранены:")
        for fmt, path in saved_paths:
            print(f"      {fmt:<4} : {path}")
        print()


# ---------------------------------------------------------
# Главный вход (legacy — не используется monitor.py, но оставлен для совместимости)
# ---------------------------------------------------------


def generate_report(arp: dict[str, str], netflow: dict[str, dict]) -> list[Device]:
    """
    ES-1.8.4: Legacy entry point.
    В monitor.py этот путь не используется — там свой пайплайн через FingerprintService.
    """
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
    "enrich_device_metadata", "ObservationExtractor",
]
