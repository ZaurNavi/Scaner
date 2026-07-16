#!/usr/bin/env python3
"""Pipeline Engine: автоматическое выполнение Builder'ов."""
from typing import Dict, Any, List
from platform.registry.builder_registry import BuilderRegistry

class Pipeline:
    """Автоматический Pipeline для выполнения Builder'ов."""
    
    def __init__(self):
        self._builders: List[str] = [
            "timeline_builder",
            "metrics_builder",
            "features_builder",
            "facts_builder"
        ]
    
    def run(self, device_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Выполняет полный Pipeline.
        
        Args:
            device_id: Идентификатор устройства
            context: Дополнительный контекст
        
        Returns:
            Dict[str, Any]: Результаты выполнения
        """
        results = {}
        current_data = device_id
        
        for builder_name in self._builders:
            descriptor = BuilderRegistry.get(builder_name)
            if not descriptor:
                print(f"  [PIPELINE] ⚠️ Builder {builder_name} not registered")
                continue
            
            try:
                builder = descriptor.builder_class()
                result = builder.build(current_data)
                results[builder_name] = result
                current_data = result
            except Exception as e:
                print(f"  [PIPELINE] ❌ Builder {builder_name} failed: {e}")
                break
        
        return results
