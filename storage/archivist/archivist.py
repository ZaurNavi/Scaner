from __future__ import annotations
import time
from .repository import Repository
from storage.schema import SnapshotBundle

class Archivist:
    """
    Активный компонент системы, который управляет сохранением данных.
    Обеспечивает безопасное сохранение с обработкой ошибок и логированием.
    """
    
    def __init__(self, repository: Repository):
        self.repo = repository
        self._stats = {
            "bundles_saved": 0,
            "total_observations": 0,
            "total_time_ms": 0.0
        }
    
    def save(self, bundle: SnapshotBundle) -> bool:
        """
        Сохраняет один SnapshotBundle с обработкой ошибок.
        Возвращает True если успешно, False если ошибка.
        """
        start_time = time.time()
        
        try:
            self.repo.save_bundle(bundle)
            
            elapsed_ms = (time.time() - start_time) * 1000
            self._stats["bundles_saved"] += 1
            self._stats["total_observations"] += len(bundle.observations)
            self._stats["total_time_ms"] += elapsed_ms
            
            return True
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            print(f"[ARCHIVIST] ❌ Save failed for bundle: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Возвращает статистику работы Архивиста."""
        return self._stats.copy()
    
    def print_summary(self):
        """Печатает итоговую статистику."""
        stats = self.get_stats()
        print(f"[ARCHIVIST] 📊 Summary:")
        print(f"  Bundles saved: {stats['bundles_saved']}")
        print(f"  Total observations: {stats['total_observations']}")
        print(f"  Total time: {stats['total_time_ms']:.1f} ms")
