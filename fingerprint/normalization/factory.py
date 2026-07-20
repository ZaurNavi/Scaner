#!/usr/bin/env python3
"""
ObservationFactory.
ES-1.8.3: Factory знает только доменные атрибуты, а не протоколы.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List

from .models import Observation, ObservationMetadata
from .registry import AttributeRegistry


class ObservationFactory:
    @staticmethod
    def create(
        collector_id: str,
        protocol: str,
        device_id: str,
        attribute: str,
        value: Any,
        metadata: ObservationMetadata = None
    ) -> Observation:
        """
        Создает и валидирует Observation.
        ES-1.8.3: Валидация перед возвратом.
        """
        if not AttributeRegistry.validate(attribute, value):
            raise ValueError(f"Invalid attribute '{attribute}' or value type {type(value)}")

        return Observation(
            contract_version=1,
            observation_id=Observation.generate_id(collector_id, device_id, attribute, value),
            collector_id=collector_id,
            protocol=protocol,
            device_id=device_id,
            attribute=attribute,
            value=value,
            timestamp=datetime.now(),
            metadata=metadata or ObservationMetadata()
        )

    @staticmethod
    def create_hostname(collector_id: str, protocol: str, device_id: str, hostname: str) -> Observation:
        return ObservationFactory.create(
            collector_id, protocol, device_id, "hostname", hostname,
            ObservationMetadata(hostname=hostname)
        )

    @staticmethod
    def create_open_ports(collector_id: str, protocol: str, device_id: str, ports: List[int]) -> Observation:
        return ObservationFactory.create(
            collector_id, protocol, device_id, "open_ports", ports,
            ObservationMetadata()
        )
        
    @staticmethod
    def create_ttl(collector_id: str, protocol: str, device_id: str, ttl: int, latency: float) -> Observation:
        return ObservationFactory.create(
            collector_id, protocol, device_id, "ttl", ttl,
            ObservationMetadata(extra=(("latency_ms", str(latency)),))
        )
