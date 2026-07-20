#!/usr/bin/env python3
"""
FingerprintService — единственный публичный API Fingerprint.
ES-1.8.2: Monitor работает исключительно с FingerprintService.

Архитектурные принципы:
- FingerprintService — единственная публичная точка входа
- Pipeline остаётся внутренней реализацией Service
- Monitor никогда не импортирует Pipeline
- Fingerprint ничего не знает о Platform
"""

from __future__ import annotations

from typing import List, Optional

from models import Device
from configuration import ConfigurationManager

from .pipeline import FingerprintContext, FingerprintPipeline, UnifiedObservationBatch


class FingerprintService:
    """
    Единственный публичный API Fingerprint.
    
    ES-1.8.2:
    - Monitor работает исключительно с FingerprintService
    - Pipeline остаётся внутренней реализацией Service
    - Fingerprint ничего не знает о Platform
    
    Использование:
        service = FingerprintService(configuration)
        batch = service.execute(ips, devices)
    """
    
    def __init__(self, configuration: ConfigurationManager):
        """
        Dependency Injection через ConfigurationManager.
        
        Args:
            configuration: ConfigurationManager для всех зависимостей
        """
        self.config = configuration
        self._pipeline = FingerprintPipeline(configuration)
    
    def execute(
        self,
        ips: List[str],
        devices: List[Device],
        metadata: Optional[dict] = None
    ) -> UnifiedObservationBatch:
        """
        Выполняет полный цикл обработки Fingerprint.
        
        Args:
            ips: Список IP-адресов
            devices: Список устройств
            metadata: Опциональные метаданные
        
        Returns:
            UnifiedObservationBatch (immutable)
        """
        # Создаём FingerprintContext
        context = FingerprintContext.create(
            ips=ips,
            devices=devices,
            configuration=self.config,
            metadata=metadata
        )
        
        # Выполняем Pipeline
        batch = self._pipeline.execute(context)
        
        return batch
    
    def process(
        self,
        ips: List[str],
        devices: List[Device],
        metadata: Optional[dict] = None
    ) -> UnifiedObservationBatch:
        """
        Алиас для execute().
        
        Args:
            ips: Список IP-адресов
            devices: Список устройств
            metadata: Опциональные метаданные
        
        Returns:
            UnifiedObservationBatch (immutable)
        """
        return self.execute(ips, devices, metadata)
