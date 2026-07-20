#!/usr/bin/env python3
"""
Correlation Engine — объединяет факты из всех источников
и применяет правила корреляции.
ES-1.8.3: Полная миграция с CollectedData на UnifiedObservationBatch.
"""

from __future__ import annotations

from models import Device
from fingerprint import UnifiedObservationBatch

from .evidence import Evidence
from .evidence_item import EvidenceItem
from .result import CorrelationResult, ConfidenceBreakdown, MatchedRule
from .rules import ALL_RULES


class CorrelationEngine:
    """
    Движок корреляции.
    """

    def correlate(self, device: Device, batch: UnifiedObservationBatch) -> CorrelationResult:
        """
        ES-1.8.3: Применяет корреляцию к устройству на основе UnifiedObservationBatch.
        """
        # 1. Собираем Evidence из Batch
        evidence = Evidence.from_device(device, batch)

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
        # Ищем Omada информацию в Batch
        omada_obs = batch.by_collector("omada").by_attribute("omada_info").filter(
            lambda o: o.metadata.ip == device.ip
        ).first()

        if omada_obs and isinstance(omada_obs.normalized_value, dict):
            entity = omada_obs.normalized_value
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
            device, batch, result
        )

        # 6. Fingerprint Score
        result.fingerprint_score = result.breakdown.total()

        # 7. Финальный confidence — из breakdown
        result.confidence = result.breakdown.total()

        return result

    def _calculate_breakdown_and_evidence(
        self,
        device: Device,
        batch: UnifiedObservationBatch,
        result: CorrelationResult,
    ) -> tuple[ConfidenceBreakdown, list[EvidenceItem]]:
        """
        ES-1.8.3: Считает ConfidenceBreakdown и собирает Evidence Items из Batch.
        """
        b = ConfidenceBreakdown()
        items: list[EvidenceItem] = []

        # Helper для извлечения значения и самого объекта Observation
        def get_obs(collector_id: str, attribute: str):
            return batch.by_collector(collector_id).by_attribute(attribute).filter(
                lambda o: o.metadata.ip == device.ip
            ).first()

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
        ttl_obs = get_obs("ttl", "ttl")
        if ttl_obs and ttl_obs.normalized_value is not None:
            conf = int(ttl_obs.confidence * 100)
            if not any("ttl" in r.name.lower() for r in result.matched_rules):
                b.ttl = conf
                items.append(EvidenceItem(
                    description=f"TTL = {ttl_obs.normalized_value} → OS inference",
                    contribution=conf,
                    source="ttl",
                ))

        # TCP
        tcp_obs = get_obs("tcp", "open_ports")
        if tcp_obs and isinstance(tcp_obs.normalized_value, list):
            conf = int(tcp_obs.confidence * 100)
            b.tcp = int(conf * 0.7)
            open_ports = tcp_obs.normalized_value[:5]
            if open_ports:
                items.append(EvidenceItem(
                    description=f"TCP ports: {', '.join(map(str, open_ports))}",
                    contribution=b.tcp,
                    source="tcp",
                ))

        # HTTP
        http_obs = get_obs("http", "http_services")
        if http_obs and isinstance(http_obs.normalized_value, dict):
            conf = int(http_obs.confidence * 100)
            b.http = conf
            server = ""
            title = ""
            for port, data in http_obs.normalized_value.items():
                if isinstance(data, dict):
                    server = data.get("server", "") or server
                    title = data.get("title", "") or title
            details = []
            if server: details.append(f"server: {server}")
            if title: details.append(f"title: {title}")
            if details:
                items.append(EvidenceItem(
                    description="HTTP response",
                    contribution=b.http,
                    source="http",
                    details=", ".join(details),
                ))

        # mDNS
        mdns_hostname = get_obs("mdns", "hostname")
        mdns_model = get_obs("mdns", "model")
        mdns_device_type = get_obs("mdns", "device_type")
        if mdns_hostname or mdns_model or mdns_device_type:
            b.mdns = 35
            details = []
            if mdns_hostname and mdns_hostname.normalized_value: details.append(f"hostname: {mdns_hostname.normalized_value}")
            if mdns_model and mdns_model.normalized_value: details.append(f"model: {mdns_model.normalized_value}")
            if mdns_device_type and mdns_device_type.normalized_value: details.append(f"type: {mdns_device_type.normalized_value}")
            if details:
                items.append(EvidenceItem(
                    description="mDNS response",
                    contribution=35,
                    source="mdns",
                    details=", ".join(details),
                ))

        # === OMADA (v1.5.0) ===
        omada_obs = get_obs("omada", "omada_info")
        if omada_obs and isinstance(omada_obs.normalized_value, dict):
            entity = omada_obs.normalized_value
            omada_device_type = (entity.get("deviceType") or "").lower()
            omada_hostname_lower = (entity.get("hostName") or entity.get("name") or "").lower()
            omada_display_name = entity.get("hostName") or entity.get("name") or ""

            is_known = ("android" in omada_device_type or "redmi" in omada_hostname_lower or "xiaomi" in omada_hostname_lower or
                        "galaxy" in omada_hostname_lower or "samsung" in omada_hostname_lower or
                        "ios" in omada_device_type or "iphone" in omada_hostname_lower or "ipad" in omada_hostname_lower or
                        "windows" in omada_device_type or "macos" in omada_device_type or "macbook" in omada_hostname_lower)

            if is_known or (omada_device_type and omada_device_type != "unknown"):
                b.omada = 70
            elif omada_display_name:
                b.omada = 30
            else:
                b.omada = 0

            details = []
            if omada_device_type: details.append(f"type: {omada_device_type}")
            if omada_display_name: details.append(f"hostname: {omada_display_name}")
            if entity.get("apName"): details.append(f"AP: {entity['apName']}")
            if entity.get("apMac"): details.append(f"AP-MAC: {entity['apMac']}")
            if entity.get("ssid"): details.append(f"SSID: {entity['ssid']}")
            if entity.get("vid"): details.append(f"VLAN: {entity['vid']}")
            if entity.get("rssi"): details.append(f"RSSI: {entity['rssi']}dBm")
            if entity.get("signalLevel"): details.append(f"Signal: {entity['signalLevel']}")
            if entity.get("channel"): details.append(f"Ch: {entity['channel']}")
            if entity.get("radioId") is not None:
                radio_name = "5GHz" if entity['radioId'] == 1 else "2.4GHz" if entity['radioId'] == 0 else f"Radio{entity['radioId']}"
                details.append(f"Radio: {radio_name}")
            if entity.get("txRate"):
                tx_mbps = entity['txRate'] / 1000 if entity['txRate'] > 100 else entity['txRate']
                details.append(f"TX: {tx_mbps:.0f}Mbps")
            if entity.get("rxRate"):
                rx_mbps = entity['rxRate'] / 1000 if entity['rxRate'] > 100 else entity['rxRate']
                details.append(f"RX: {rx_mbps:.0f}Mbps")
            if entity.get("wifiMode") is not None:
                wifi_modes = {0: "802.11b", 1: "802.11g", 2: "802.11a", 3: "802.11n", 4: "802.11ac", 5: "802.11ax"}
                details.append(f"WiFi: {wifi_modes.get(entity['wifiMode'], f'Mode{entity["wifiMode"]}')}" )
            if entity.get("connectType") is not None:
                conn_types = {0: "wired", 1: "wireless"}
                details.append(f"Conn: {conn_types.get(entity['connectType'], f'Type{entity["connectType"]}')}")
            if entity.get("connectDevType"): details.append(f"ConnTo: {entity['connectDevType']}")
            if entity.get("authStatus") is not None:
                details.append(f"Auth: {'authenticated' if entity['authStatus'] == 0 else f'auth:{entity["authStatus"]}'}")
            if entity.get("uptime"): details.append(f"Uptime: {entity['uptime'] // 60}min")
            if entity.get("lastSeen"): details.append(f"LastSeen: {entity['lastSeen']}")
            if entity.get("active") is not None: details.append(f"Active: {entity['active']}")
            if entity.get("trafficDown"): details.append(f"Down: {entity['trafficDown'] / (1024 * 1024):.1f}MB")
            if entity.get("trafficUp"): details.append(f"Up: {entity['trafficUp'] / (1024 * 1024):.1f}MB")
            if entity.get("downPacket"): details.append(f"PktDown: {entity['downPacket']}")
            if entity.get("upPacket"): details.append(f"PktUp: {entity['upPacket']}")
            if entity.get("powerSave") is not None: details.append(f"PowerSave: {entity['powerSave']}")
            if entity.get("wireless") is not None: details.append(f"Wireless: {entity['wireless']}")
            if entity.get("guest") is not None: details.append(f"Guest: {entity['guest']}")

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
