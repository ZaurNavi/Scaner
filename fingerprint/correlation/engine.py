#!/usr/bin/env python3
"""
Correlation Engine — объединяет факты из всех источников
и применяет правила корреляции.
"""

from __future__ import annotations

from models import Device
from fingerprint.collectors.base import CollectedData

from .evidence import Evidence
from .evidence_item import EvidenceItem
from .result import CorrelationResult, ConfidenceBreakdown, MatchedRule
from .rules import ALL_RULES


class CorrelationEngine:
    """
    Движок корреляции.
    """

    def correlate(self, device: Device, collected: CollectedData) -> CorrelationResult:
        """
        Применяет корреляцию к устройству.
        """
        # 1. Собираем Evidence
        evidence = Evidence.from_device(device, collected)

        # 2. Применяем все правила
        result = CorrelationResult()

        for rule in ALL_RULES:
            if rule.matches(evidence):
                then = rule.then
                rule_confidence = then.get("confidence", 0)
                rule_reason = then.get("reason", "")

                # Сохраняем информацию о правиле как MatchedRule
                result.matched_rules.append(
                    MatchedRule(
                        name=rule.name,
                        confidence=rule_confidence,
                        reason=rule_reason,
                        priority=rule.priority,
                    )
                )

                # Берём правило с максимальным confidence
                if rule_confidence > result.confidence:
                    if then.get("os"):
                        result.os = then["os"]
                    if then.get("model"):
                        result.model = then["model"]
                    if then.get("device_type"):
                        result.device_type = then["device_type"]
                    if then.get("vendor"):
                        result.vendor = then["vendor"]
                    result.confidence = rule_confidence
                    if rule_reason:
                        result.reasons.append(rule_reason)

        # 3. === OMADA ENRICHMENT (v1.5.0) ===
        # Если Omada знает тип устройства — используем это как сильный сигнал
        # Omada имеет приоритет над TTL, так как контроллер видит реальные данные
        if "omada" in collected.sources:
            omada_result = collected.sources["omada"]
            entities = omada_result.raw_data.get("entities", [])
            if entities:
                entity = entities[0]  # Берём первую запись (обычно одна на IP)
                omada_device_type = (entity.get("deviceType") or "").lower()
                omada_hostname = entity.get("hostName") or entity.get("name") or ""
                
                # Omada знает, что это Android
                if "android" in omada_device_type:
                    result.os = "Android"
                    result.device_type = "Smartphone"
                    result.confidence = max(result.confidence, 70)
                    if omada_hostname:
                        result.reasons.append(f"Omada: Android device ({omada_hostname})")
                    else:
                        result.reasons.append("Omada: Android device")
                
                # Omada знает, что это iOS
                elif "ios" in omada_device_type or "iphone" in omada_hostname.lower() or "ipad" in omada_hostname.lower():
                    result.os = "iOS"
                    result.device_type = "Smartphone" if "iphone" in omada_hostname.lower() else "Tablet"
                    result.confidence = max(result.confidence, 70)
                    if omada_hostname:
                        result.reasons.append(f"Omada: iOS device ({omada_hostname})")
                    else:
                        result.reasons.append("Omada: iOS device")
                
                # Omada знает, что это Windows
                elif "windows" in omada_device_type or "pc" in omada_device_type:
                    result.os = "Windows"
                    result.device_type = "Desktop" if "pc" in omada_device_type else "Laptop"
                    result.confidence = max(result.confidence, 70)
                    if omada_hostname:
                        result.reasons.append(f"Omada: Windows device ({omada_hostname})")
                    else:
                        result.reasons.append("Omada: Windows device")
                
                # Omada знает, что это macOS
                elif "macos" in omada_device_type or "mac" in omada_hostname.lower():
                    result.os = "macOS"
                    result.device_type = "Laptop" if "macbook" in omada_hostname.lower() else "Desktop"
                    result.confidence = max(result.confidence, 70)
                    if omada_hostname:
                        result.reasons.append(f"Omada: macOS device ({omada_hostname})")
                    else:
                        result.reasons.append("Omada: macOS device")
        # ========================================

        # 4. Пост-обработка vendor
        if not result.vendor and device.vendor and device.vendor != "Unknown":
            result.vendor = device.vendor

        # 5. Считаем ConfidenceBreakdown и собираем Evidence Items
        result.breakdown, result.evidence_items = self._calculate_breakdown_and_evidence(
            device, collected, result
        )

        # 6. Fingerprint Score
        result.fingerprint_score = result.breakdown.total()

        # 7. Финальный confidence — из breakdown
        result.confidence = result.breakdown.total()

        return result

    def _calculate_breakdown_and_evidence(
        self,
        device: Device,
        collected: CollectedData,
        result: CorrelationResult,
    ) -> tuple[ConfidenceBreakdown, list[EvidenceItem]]:
        """
        Считает ConfidenceBreakdown и собирает Evidence Items.
        """
        b = ConfidenceBreakdown()
        items: list[EvidenceItem] = []

        # Vendor
        if device.vendor and device.vendor != "Unknown":
            b.vendor = 10
            items.append(EvidenceItem(
                description=f"Vendor = {device.vendor}",
                contribution=10,
                source="vendor",
                details=f"MAC: {device.mac[:8]}",
            ))

        # Hostname
        if device.hostname:
            b.hostname = 10
            items.append(EvidenceItem(
                description=f"Hostname = {device.hostname}",
                contribution=10,
                source="hostname",
            ))

        # TTL
        ttl_result = collected.sources.get("ttl")
        if ttl_result and ttl_result.os:
            if not any("ttl" in r.name.lower() for r in result.matched_rules):
                b.ttl = ttl_result.confidence
                items.append(EvidenceItem(
                    description=f"TTL = {ttl_result.ttl} → {ttl_result.os}",
                    contribution=ttl_result.confidence,
                    source="ttl",
                    details=f"latency: {ttl_result.latency_ms}ms",
                ))

        # TCP
        tcp_result = collected.sources.get("tcp")
        if tcp_result and tcp_result.device_type:
            b.tcp = int(tcp_result.confidence * 0.7)
            open_ports = [p for p, info in tcp_result.services.items() if info.get("state") == "open"]
            if open_ports:
                items.append(EvidenceItem(
                    description=f"TCP ports: {', '.join(map(str, open_ports[:5]))}",
                    contribution=b.tcp,
                    source="tcp",
                    details=f"device_type: {tcp_result.device_type}",
                ))

        # HTTP
        http_result = collected.sources.get("http")
        if http_result and http_result.confidence:
            b.http = http_result.confidence
            server = ""
            title = ""
            for port, data in http_result.services.items():
                if isinstance(data, dict):
                    server = data.get("server", "") or server
                    title = data.get("title", "") or title
            details = []
            if server:
                details.append(f"server: {server}")
            if title:
                details.append(f"title: {title}")
            items.append(EvidenceItem(
                description="HTTP response",
                contribution=b.http,
                source="http",
                details=", ".join(details),
            ))

        # mDNS
        if collected.mdns.hostname or collected.mdns.model or collected.mdns.device_type:
            b.mdns = 35
            details = []
            if collected.mdns.hostname:
                details.append(f"hostname: {collected.mdns.hostname}")
            if collected.mdns.model:
                details.append(f"model: {collected.mdns.model}")
            if collected.mdns.device_type:
                details.append(f"type: {collected.mdns.device_type}")
            items.append(EvidenceItem(
                description="mDNS response",
                contribution=35,
                source="mdns",
                details=", ".join(details),
            ))

        # === OMADA (v1.5.0) ===
        if "omada" in collected.sources:
            omada_result = collected.sources["omada"]
            entities = omada_result.raw_data.get("entities", [])
            if entities:
                entity = entities[0]
                omada_device_type = (entity.get("deviceType") or "").lower()
                omada_hostname = entity.get("hostName") or entity.get("name") or ""
                omada_ap_name = entity.get("apName") or ""
                omada_ssid = entity.get("ssid") or ""
                omada_rssi = entity.get("rssi") or entity.get("signalLevel")
                
                # Omada даёт сильный сигнал (70), если знает тип устройства
                if omada_device_type and omada_device_type != "unknown":
                    b.omada = 70
                    details = []
                    details.append(f"type: {omada_device_type}")
                    if omada_hostname:
                        details.append(f"hostname: {omada_hostname}")
                    if omada_ap_name:
                        details.append(f"AP: {omada_ap_name}")
                    if omada_ssid:
                        details.append(f"SSID: {omada_ssid}")
                    if omada_rssi:
                        details.append(f"RSSI: {omada_rssi}dBm")
                    
                    items.append(EvidenceItem(
                        description=f"Omada Controller identifies device",
                        contribution=70,
                        source="omada",
                        details=", ".join(details),
                    ))
                # Если Omada не знает тип, но есть hostname — слабый сигнал (30)
                elif omada_hostname:
                    b.omada = 30
                    details = [f"hostname: {omada_hostname}"]
                    if omada_ap_name:
                        details.append(f"AP: {omada_ap_name}")
                    if omada_ssid:
                        details.append(f"SSID: {omada_ssid}")
                    if omada_rssi:
                        details.append(f"RSSI: {omada_rssi}dBm")
                    
                    items.append(EvidenceItem(
                        description=f"Omada Controller provides hostname",
                        contribution=30,
                        source="omada",
                        details=", ".join(details),
                    ))
        # ======================

        # Correlation (правила)
        if result.matched_rules:
            b.correlation = result.confidence
            for rule in result.matched_rules:
                items.append(EvidenceItem(
                    description=f"Rule: {rule.name}",
                    contribution=rule.confidence,
                    source=f"rule:{rule.name}",
                    details=rule.reason,
                ))

        return b, items


# Глобальный экземпляр
engine = CorrelationEngine()
