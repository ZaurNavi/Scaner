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
        # Если Omada знает тип устройства или содержит ключевые слова в hostname
        if "omada" in collected.sources:
            omada_result = collected.sources["omada"]
            entities = omada_result.raw_data.get("entities", [])
            if entities:
                entity = entities[0]
                omada_device_type = (entity.get("deviceType") or "").lower()
                omada_hostname_lower = (entity.get("hostName") or entity.get("name") or "").lower()
                omada_display_name = entity.get("hostName") or entity.get("name") or ""
                
                # Умная эвристика: определяем ОС по типу или по ключевым словам в имени
                is_android = ("android" in omada_device_type or 
                              "redmi" in omada_hostname_lower or 
                              "xiaomi" in omada_hostname_lower or 
                              "galaxy" in omada_hostname_lower or 
                              "samsung" in omada_hostname_lower)
                
                is_ios = ("ios" in omada_device_type or 
                          "iphone" in omada_hostname_lower or 
                          "ipad" in omada_hostname_lower or 
                          "apple" in omada_hostname_lower)
                
                is_windows = ("windows" in omada_device_type or 
                              "pc" in omada_hostname_lower or 
                              "desktop" in omada_hostname_lower)
                
                is_macos = ("macos" in omada_device_type or 
                            "macbook" in omada_hostname_lower or 
                            "imac" in omada_hostname_lower)

                if is_android:
                    result.os = "Android"
                    result.device_type = "Smartphone"
                    result.confidence = max(result.confidence, 70)
                    result.reasons.append(f"Omada: Android device ({omada_display_name})")
                
                elif is_ios:
                    result.os = "iOS"
                    result.device_type = "Smartphone" if "iphone" in omada_hostname_lower else "Tablet"
                    result.confidence = max(result.confidence, 70)
                    result.reasons.append(f"Omada: iOS device ({omada_display_name})")
                
                elif is_windows:
                    result.os = "Windows"
                    result.device_type = "Desktop" if "pc" in omada_hostname_lower or "desktop" in omada_hostname_lower else "Laptop"
                    result.confidence = max(result.confidence, 70)
                    result.reasons.append(f"Omada: Windows device ({omada_display_name})")
                
                elif is_macos:
                    result.os = "macOS"
                    result.device_type = "Laptop" if "macbook" in omada_hostname_lower else "Desktop"
                    result.confidence = max(result.confidence, 70)
                    result.reasons.append(f"Omada: macOS device ({omada_display_name})")
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
                omada_hostname_lower = (entity.get("hostName") or entity.get("name") or "").lower()
                omada_display_name = entity.get("hostName") or entity.get("name") or ""
                
                # Проверяем, распознали ли мы устройство по типу или по ключевым словам в имени
                is_known = ("android" in omada_device_type or "redmi" in omada_hostname_lower or "xiaomi" in omada_hostname_lower or 
                            "galaxy" in omada_hostname_lower or "samsung" in omada_hostname_lower or
                            "ios" in omada_device_type or "iphone" in omada_hostname_lower or "ipad" in omada_hostname_lower or
                            "windows" in omada_device_type or "macos" in omada_device_type or "macbook" in omada_hostname_lower)
                
                # Если устройство распознано (или тип известен и не "unknown") — даём сильный сигнал 70
                if is_known or (omada_device_type and omada_device_type != "unknown"):
                    b.omada = 70
                elif omada_display_name:
                    b.omada = 30
                else:
                    b.omada = 0
                
                # === РАСШИРЕННОЕ ОТОБРАЖЕНИЕ ВСЕХ ПОЛЕЙ ОМАДА ===
                details = []
                
                # Базовая информация
                if omada_device_type:
                    details.append(f"type: {omada_device_type}")
                if omada_display_name:
                    details.append(f"hostname: {omada_display_name}")
                
                # Сетевая инфраструктура
                if entity.get("apName"):
                    details.append(f"AP: {entity['apName']}")
                if entity.get("apMac"):
                    details.append(f"AP-MAC: {entity['apMac']}")
                if entity.get("ssid"):
                    details.append(f"SSID: {entity['ssid']}")
                if entity.get("vid"):
                    details.append(f"VLAN: {entity['vid']}")
                
                # Радио и сигнал
                if entity.get("rssi"):
                    details.append(f"RSSI: {entity['rssi']}dBm")
                if entity.get("signalLevel"):
                    details.append(f"Signal: {entity['signalLevel']}")
                if entity.get("signalRank"):
                    details.append(f"Rank: {entity['signalRank']}")
                if entity.get("snr"):
                    details.append(f"SNR: {entity['snr']}dB")
                
                # Канал и радио
                if entity.get("channel"):
                    details.append(f"Ch: {entity['channel']}")
                if entity.get("radioId") is not None:
                    radio_name = "5GHz" if entity['radioId'] == 1 else "2.4GHz" if entity['radioId'] == 0 else f"Radio{entity['radioId']}"
                    details.append(f"Radio: {radio_name}")
                
                # Скорости (в Kbps из API, конвертируем в Mbps)
                if entity.get("txRate"):
                    tx_mbps = entity['txRate'] / 1000 if entity['txRate'] > 100 else entity['txRate']
                    details.append(f"TX: {tx_mbps:.0f}Mbps")
                if entity.get("rxRate"):
                    rx_mbps = entity['rxRate'] / 1000 if entity['rxRate'] > 100 else entity['rxRate']
                    details.append(f"RX: {rx_mbps:.0f}Mbps")
                
                # WiFi режим
                if entity.get("wifiMode") is not None:
                    wifi_modes = {0: "802.11b", 1: "802.11g", 2: "802.11a", 3: "802.11n", 4: "802.11ac", 5: "802.11ax"}
                    wifi_name = wifi_modes.get(entity['wifiMode'], f"Mode{entity['wifiMode']}")
                    details.append(f"WiFi: {wifi_name}")
                
                # Статус подключения
                if entity.get("connectType") is not None:
                    conn_types = {0: "wired", 1: "wireless"}
                    conn_type = conn_types.get(entity['connectType'], f"Type{entity['connectType']}")
                    details.append(f"Conn: {conn_type}")
                if entity.get("connectDevType"):
                    details.append(f"ConnTo: {entity['connectDevType']}")
                
                # Аутентификация
                if entity.get("authStatus") is not None:
                    auth_status = "authenticated" if entity['authStatus'] == 0 else f"auth:{entity['authStatus']}"
                    details.append(f"Auth: {auth_status}")
                
                # Время и активность
                if entity.get("uptime"):
                    uptime_min = entity['uptime'] // 60
                    details.append(f"Uptime: {uptime_min}min")
                if entity.get("lastSeen"):
                    details.append(f"LastSeen: {entity['lastSeen']}")
                if entity.get("active") is not None:
                    details.append(f"Active: {entity['active']}")
                
                # Трафик (в байтах, конвертируем в MB)
                if entity.get("trafficDown"):
                    down_mb = entity['trafficDown'] / (1024 * 1024)
                    details.append(f"Down: {down_mb:.1f}MB")
                if entity.get("trafficUp"):
                    up_mb = entity['trafficUp'] / (1024 * 1024)
                    details.append(f"Up: {up_mb:.1f}MB")
                
                # Пакеты
                if entity.get("downPacket"):
                    details.append(f"PktDown: {entity['downPacket']}")
                if entity.get("upPacket"):
                    details.append(f"PktUp: {entity['upPacket']}")
                
                # Дополнительно
                if entity.get("powerSave") is not None:
                    details.append(f"PowerSave: {entity['powerSave']}")
                if entity.get("wireless") is not None:
                    details.append(f"Wireless: {entity['wireless']}")
                if entity.get("guest") is not None:
                    details.append(f"Guest: {entity['guest']}")
                
                # Добавляем Evidence Item
                if details:
                    desc = "Omada Controller identifies device" if (is_known or (omada_device_type and omada_device_type != "unknown")) else "Omada Controller provides telemetry"
                    items.append(EvidenceItem(
                        description=desc,
                        contribution=b.omada,
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
