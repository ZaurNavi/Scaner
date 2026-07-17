#!/usr/bin/env python3
"""ProfileDiffer — ядро Change Detection Layer."""
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Set
from types import MappingProxyType

from ..profile import UnifiedDeviceProfile
from .enums import ChangeType, CapabilityState
from .exceptions import DifferentIdentityError, InvalidProfileError
from .models import (
    ProfileDiff, EMPTY_DIFF, SummaryDiff, MetricDelta, 
    EngineDiff, CapabilityDiff, Change
)
from .indexer import ProfileIndexer

class ProfileDiffer:
    """
    Сравнивает две версии UnifiedDeviceProfile и возвращает детерминированный, 
    полностью иммутабельный ProfileDiff.
    Все операции сравнения имеют сложность O(n).
    """

    def compare(self, old_profile: UnifiedDeviceProfile, new_profile: UnifiedDeviceProfile) -> ProfileDiff:
        if not isinstance(old_profile, UnifiedDeviceProfile) or not isinstance(new_profile, UnifiedDeviceProfile):
            raise InvalidProfileError("Both arguments must be instances of UnifiedDeviceProfile")
        
        if old_profile.identity.device_uuid != new_profile.identity.device_uuid:
            raise DifferentIdentityError(
                f"Cannot compare different devices: {old_profile.identity.device_uuid} != {new_profile.identity.device_uuid}"
            )

        # Идемпотентность: если версии профилей идентичны, возвращаем EMPTY_DIFF
        if old_profile.version_snapshot.to_cache_key() == new_profile.version_snapshot.to_cache_key():
            return EMPTY_DIFF

        return self._build_diff(old_profile, new_profile)

    def _build_diff(self, old: UnifiedDeviceProfile, new: UnifiedDeviceProfile) -> ProfileDiff:
        now = datetime.now()
        changes: List[Change] = []

        # 1. Индексация для O(n) сравнения (делегировано Indexer)
        old_facts = ProfileIndexer.index_facts(old)
        new_facts = ProfileIndexer.index_facts(new)
        old_engines = set(ProfileIndexer.index_engines(old))
        new_engines = set(ProfileIndexer.index_engines(new))
        old_caps = ProfileIndexer.index_capabilities(old)
        new_caps = ProfileIndexer.index_capabilities(new)

        # 2. Сравнение Summary
        summary_diff = self._compare_summary(old.summary, new.summary, changes, now)

        # 3. Сравнение Engines
        engine_diff = self._compare_engines(old_engines, new_engines, changes, now)

        # 4. Сравнение Capabilities
        capability_diff = self._compare_capabilities(old_caps, new_caps, changes, now)

        # 5. Сравнение Facts (O(n))
        self._compare_facts(old_facts, new_facts, changes, now)

        # 6. Детерминированный diff_id
        diff_id = self._generate_deterministic_id(old, new)

        # 7. Сборка иммутабельного ProfileDiff
        return ProfileDiff(
            identity_uuid=old.identity.device_uuid,
            diff_id=diff_id,
            created_at=now,
            summary=summary_diff,
            engine_diff=engine_diff,
            capability_diff=capability_diff,
            changes=tuple(changes)  # Преобразуем в tuple для гарантии иммутабельности
        )

    def _generate_deterministic_id(self, old: UnifiedDeviceProfile, new: UnifiedDeviceProfile) -> str:
        old_v = str(old.version_snapshot.to_cache_key())
        new_v = str(new.version_snapshot.to_cache_key())
        uuid = old.identity.device_uuid
        payload = f"{uuid}|{old_v}|{new_v}".encode('utf-8')
        return hashlib.sha256(payload).hexdigest()[:16]

    def _compare_summary(self, old_sum, new_sum, changes: List[Change], now: datetime) -> SummaryDiff:
        def make_delta(old_val, new_val, subject: str):
            delta = (new_val - old_val) if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)) else None
            if old_val != new_val:
                changes.append(self._make_change(
                    ChangeType.UPDATED, "summary", "system", "general", old_val, new_val, delta, now, {}
                ))
            return MetricDelta(old=old_val, new=new_val, delta=delta)

        old_last = old_sum.last_seen.isoformat() if old_sum.last_seen else None
        new_last = new_sum.last_seen.isoformat() if new_sum.last_seen else None

        return SummaryDiff(
            history_depth=make_delta(old_sum.history_depth, new_sum.history_depth, "history_depth"),
            facts_count=make_delta(old_sum.facts, new_sum.facts, "facts_count"),
            sessions=make_delta(old_sum.sessions, new_sum.sessions, "sessions"),
            confidence=make_delta(old_sum.confidence, new_sum.confidence, "confidence"),
            last_seen=make_delta(old_last, new_last, "last_seen")
        )

    def _compare_engines(self, old_eng: Set[str], new_eng: Set[str], changes: List[Change], now: datetime) -> EngineDiff:
        added = tuple(sorted(new_eng - old_eng))
        removed = tuple(sorted(old_eng - new_eng))
        
        for eng in added:
            changes.append(self._make_change(ChangeType.ADDED, "engine", eng, "system", None, eng, None, now, {}))
        for eng in removed:
            changes.append(self._make_change(ChangeType.REMOVED, "engine", eng, "system", eng, None, None, now, {}))
            
        return EngineDiff(added=added, removed=removed)

    def _compare_capabilities(self, old_caps: Dict[str, CapabilityState], new_caps: Dict[str, CapabilityState], 
                              changes: List[Change], now: datetime) -> CapabilityDiff:
        all_caps = set(old_caps.keys()) | set(new_caps.keys())
        became_avail = []
        became_unavail = []
        state_changed = []

        for cap in all_caps:
            old_state = old_caps.get(cap, CapabilityState.NOT_AVAILABLE)
            new_state = new_caps.get(cap, CapabilityState.NOT_AVAILABLE)
            
            if old_state != new_state:
                if new_state == CapabilityState.AVAILABLE:
                    became_avail.append(cap)
                    ctype = ChangeType.ADDED
                elif new_state == CapabilityState.NOT_AVAILABLE:
                    became_unavail.append(cap)
                    ctype = ChangeType.REMOVED
                else:
                    state_changed.append(cap)
                    ctype = ChangeType.UPDATED
                
                changes.append(self._make_change(
                    ctype, "capability", "system", cap, old_state.value, new_state.value, None, now, {}
                ))

        return CapabilityDiff(
            became_available=tuple(sorted(became_avail)),
            became_unavailable=tuple(sorted(became_unavail)),
            state_changed=tuple(sorted(state_changed))
        )

    def _compare_facts(self, old_facts: Dict[str, Dict], new_facts: Dict[str, Dict], changes: List[Change], now: datetime):
        all_ids = set(old_facts.keys()) | set(new_facts.keys())
        
        for fact_id in all_ids:
            old_f = old_facts.get(fact_id)
            new_f = new_facts.get(fact_id)
            
            if old_f and not new_f:
                changes.append(self._make_fact_change(ChangeType.REMOVED, old_f, None, now))
            elif new_f and not old_f:
                changes.append(self._make_fact_change(ChangeType.ADDED, None, new_f, now))
            elif old_f and new_f:
                # Проверка на обновление полей
                changed_fields = []
                old_vals, new_vals = {}, {}
                for key in set(old_f.keys()) | set(new_f.keys()):
                    if old_f.get(key) != new_f.get(key):
                        changed_fields.append(key)
                        old_vals[key] = old_f.get(key)
                        new_vals[key] = new_f.get(key)
                
                if changed_fields:
                    changes.append(self._make_fact_change(
                        ChangeType.UPDATED, old_f, new_f, now, changed_fields, old_vals, new_vals
                    ))

    def _make_change(self, ctype: ChangeType, subject: str, engine: str, category: str, 
                     old: Any, new: Any, delta: Any, now: datetime, metadata: Dict) -> Change:
        return Change(
            change_id=hashlib.sha256(f"{subject}{ctype.value}{str(old)}{str(new)}".encode()).hexdigest()[:12],
            type=ctype,
            subject=subject,
            engine=engine,
            category=category,
            old=old,
            new=new,
            delta=delta,
            metadata=MappingProxyType(metadata)
        )

    def _make_fact_change(self, ctype: ChangeType, old_f: dict, new_f: dict, now: datetime, 
                          changed_fields: List[str] = None, old_vals: dict = None, new_vals: dict = None) -> Change:
        fact_ref = new_f if new_f else old_f
        fact_id = fact_ref["id"]
        
        metadata = {
            "fact_id": fact_id,
            "engine": fact_ref["engine"],
            "category": fact_ref["category"],
            "changed_fields": tuple(changed_fields) if changed_fields else tuple(new_f.keys()) if ctype == ChangeType.ADDED else (),
            "old_values": MappingProxyType(old_vals or (old_f if ctype == ChangeType.REMOVED else {})),
            "new_values": MappingProxyType(new_vals or (new_f if ctype == ChangeType.ADDED else {}))
        }
        
        return self._make_change(
            ctype=ctype,
            subject="fact",
            engine=fact_ref["engine"],
            category=fact_ref["category"],
            old=old_f if ctype == ChangeType.REMOVED else None,
            new=new_f if ctype == ChangeType.ADDED else None,
            delta=None,
            now=now,
            metadata=metadata
        )
