from __future__ import annotations
from typing import List
from .repository import Repository
from storage.schema import SnapshotBundle, SaveResult


class Archivist:
    """
    Активный компонент системы, который управляет сохранением данных.
    Агрегирует SaveResult из всех bundle'ов.
    """

    def __init__(self, repository: Repository):
        self.repo = repository
        self._results: List[SaveResult] = []

    def save(self, bundle: SnapshotBundle) -> SaveResult:
        """
        Сохраняет один SnapshotBundle и возвращает SaveResult.
        """
        result = self.repo.save_bundle(bundle)
        self._results.append(result)
        return result

    def get_aggregated_result(self) -> SaveResult:
        """
        Возвращает агрегированный SaveResult по всем сохранённым bundle'ам.
        """
        if not self._results:
            return SaveResult()

        total_devices_created = sum(r.devices_created for r in self._results)
        total_devices_updated = sum(r.devices_updated for r in self._results)
        total_snapshots = sum(r.snapshots_saved for r in self._results)
        total_observations = sum(r.observations_saved for r in self._results)
        total_evidence = sum(r.evidence_saved for r in self._results)
        total_capabilities = sum(r.capabilities_saved for r in self._results)
        total_sessions = sum(r.sessions_updated for r in self._results)
        total_time = sum(r.elapsed_ms for r in self._results)
        all_success = all(r.success for r in self._results)
        errors = [r.error_message for r in self._results if not r.success]

        return SaveResult(
            devices_created=total_devices_created,
            devices_updated=total_devices_updated,
            snapshots_saved=total_snapshots,
            observations_saved=total_observations,
            evidence_saved=total_evidence,
            capabilities_saved=total_capabilities,
            sessions_updated=total_sessions,
            elapsed_ms=total_time,
            success=all_success,
            error_message="; ".join(errors) if errors else "",
        )

    def print_summary(self):
        """Печатает агрегированную статистику."""
        result = self.get_aggregated_result()
        print(f"  [ARCHIVIST] 📊 Summary:")
        print(f"      Devices created:   {result.devices_created}")
        print(f"      Devices updated:   {result.devices_updated}")
        print(f"      Snapshots saved:   {result.snapshots_saved}")
        print(f"      Observations:      {result.observations_saved}")
        print(f"      Evidence:          {result.evidence_saved}")
        print(f"      Capabilities:      {result.capabilities_saved}")
        print(f"      Sessions updated:  {result.sessions_updated}")
        print(f"      Elapsed:           {result.elapsed_ms:.1f} ms")
        if not result.success:
            print(f"      ❌ Errors:         {result.error_message}")
