#!/usr/bin/env python3
"""
Correlation Engine — объединяет факты из всех источников
и применяет правила корреляции.
"""

from __future__ import annotations

from models import Device
from fingerprint.collectors.base import CollectedData

from .evidence import Evidence
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

        # 3. Пост-обработка vendor
        if not result.vendor and device.vendor and device.vendor != "Unknown":
            result.vendor = device.vendor

        # 4. Считаем ConfidenceBreakdown
        result.breakdown = self._calculate_breakdown(device, collected, result)

        # 5. Fingerprint Score
        result.fingerprint_score = result.breakdown.total()

        # 6. Финальный confidence — из breakdown
        result.confidence = result.breakdown.total()

        return result

    def _calculate_breakdown(
        self,
        device: Device,
        collected: CollectedData,
        result: CorrelationResult,
    ) -> ConfidenceBreakdown:
        """
        Считает ConfidenceBreakdown — вклад каждого источника.
        """
        b = ConfidenceBreakdown()

        # Vendor
        if device.vendor and device.vendor != "Unknown":
            b.vendor = 10

        # Hostname
        if device.hostname:
            b.hostname = 10

        # TTL
        ttl_result = collected.sources.get("ttl")
        if ttl_result and ttl_result.os:
            if not any("ttl" in r.name.lower() for r in result.matched_rules):
                b.ttl = ttl_result.confidence

        # TCP
        tcp_result = collected.sources.get("tcp")
        if tcp_result and tcp_result.device_type:
            b.tcp = int(tcp_result.confidence * 0.7)

        # HTTP
        http_result = collected.sources.get("http")
        if http_result and http_result.confidence:
            b.http = http_result.confidence

        # mDNS
        if collected.mdns.hostname or collected.mdns.model or collected.mdns.device_type:
            b.mdns = 35

        # Correlation (правила)
        if result.matched_rules:
            b.correlation = result.confidence

        return b


# Глобальный экземпляр
engine = CorrelationEngine()
