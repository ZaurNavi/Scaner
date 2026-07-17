#!/usr/bin/env python3
"""ProfileService — единственная точка построения Profile."""
import time
from datetime import datetime
from typing import Optional
from .builder import ProfileBuilder
from .cache import ProfileSnapshotCache
from .result import ProfileResult, ProfileExecution
from .profile import UnifiedDeviceProfile
from .query.api import ProfileQueryAPI
from .capability.resolver import CapabilityResolver
from ..knowledge.service import KnowledgeService
from ..cache.platform import VersionSnapshot

class ProfileService:
    """
    ProfileService — единственная точка построения Profile.
    
    Предоставляет:
    - build(): строит новый Profile
    - get(): получает из кэша
    - invalidate(): инвалидирует кэш
    - query(): возвращает Query API
    """
    
    def __init__(self, knowledge_service: KnowledgeService):
        self.knowledge_service = knowledge_service
        self.builder = ProfileBuilder(knowledge_service)
        self.cache = ProfileSnapshotCache()
    
    def build(self, device_id: str, version_snapshot: VersionSnapshot = None) -> ProfileResult:
        """Строит UnifiedDeviceProfile."""
        start_time = time.time()
        execution = ProfileExecution(
            started_at=datetime.now(),
            finished_at=datetime.now(),
            duration_ms=0.0,
            builder_version="1.0.0"  # ДОБАВЛЕНО
        )
        
        if version_snapshot is None:
            version_snapshot = VersionSnapshot()
        
        # Проверяем кэш
        cached_profile = self.cache.get(device_id, version_snapshot)
        if cached_profile:
            execution.finished_at = datetime.now()
            execution.duration_ms = (time.time() - start_time) * 1000
            execution.cache_hit = True
            return ProfileResult(profile=cached_profile, execution=execution)
        
        # Строим новый Profile
        try:
            profile = self.builder.build(device_id, version_snapshot)
            
            # Разрешаем Capabilities через Profile
            capabilities = CapabilityResolver.resolve(profile)
            
            # Создаём новый Profile с capabilities (immutable)
            from dataclasses import replace
            profile = replace(profile, capabilities=capabilities)
            
            self.cache.put(device_id, profile, version_snapshot)
            
            execution.finished_at = datetime.now()
            execution.duration_ms = (time.time() - start_time) * 1000
            execution.cache_hit = False
            
            return ProfileResult(profile=profile, execution=execution)
        except Exception as e:
            execution.finished_at = datetime.now()
            execution.duration_ms = (time.time() - start_time) * 1000
            execution.errors.append(str(e))
            raise
    
    def get(self, device_id: str, version_snapshot: VersionSnapshot = None) -> Optional[UnifiedDeviceProfile]:
        """Получает Profile из кэша."""
        if version_snapshot is None:
            version_snapshot = VersionSnapshot()
        return self.cache.get(device_id, version_snapshot)
    
    def invalidate(self, device_id: str):
        """Инвалидирует кэш для устройства."""
        self.cache.invalidate(device_id)
    
    def query(self, device_id: str) -> ProfileQueryAPI:
        """Возвращает Query API для устройства."""
        return ProfileQueryAPI(device_id, self.knowledge_service)
