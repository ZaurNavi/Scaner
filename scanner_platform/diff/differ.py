#!/usr/bin/env python3
"""ProfileDiffer — ядро Change Detection Layer."""
import uuid
from datetime import datetime
from typing import Any, Dict, List

from ..profile import UnifiedDeviceProfile
from .enums import ChangeType, Severity, ChangeReason
from .exceptions import DifferentIdentityError, InvalidProfileError, DiffBuildError
from .models import (
    ProfileDiff, SummaryDiff, SummaryMetric, EngineDiff, 
    CapabilityDiff, Change, FactChange
)
from .resolver import SeverityResolver
from .indexer import ProfileIndexer

class ProfileDiffer:
    """
    Сравнивает две версии UnifiedDeviceProfile и возвращает автономный ProfileDiff.
    Сложность всех операций сравнения: O(n).
    """
    
    def __init__(self, severity_resolver: SeverityResolver = None):
        self.resolver = severity_resolver or SeverityResolver()

    def compare(self, old_profile: UnifiedDeviceProfile, new_profile: UnifiedDeviceProfile, 
                old_facts: List[Any] = None, new_facts: List[Any] = None) -> ProfileDiff:
        """
        Сравнивает профили и возвращает ProfileDiff.
        
        :param old_facts: Список фактов старого профиля (для детального FactChange)
        :param new_facts: Список фактов нового профиля
        """
        if not isinstance(old_profile, UnifiedDeviceProfile) or not isinstance(new_profile, UnifiedDeviceProfile):
            raise InvalidProfileError("Both profiles must be instances of UnifiedDeviceProfile")
        
        if old_profile.identity.device_uuid != new_profile.identity.device_uuid:
            raise DifferentIdentityError(
                f"Cannot compare different devices: {old_profile.identity.device_uuid} != {new_profile.identity.device_uuid}"
            )
        
        try:
            return self._build_diff(old_profile, new_profile, old_facts or [], new_facts or [])
        except Exception as e:
            raise DiffBuildError(f"Failed to build diff: {e}")

    def _build_diff(self, old: UnifiedDeviceProfile, new: UnifiedDeviceProfile, 
                    old_facts: List[Any], new_facts: List[Any]) -> ProfileDiff:
        
        # 1. Индексация фактов для O(n) сравнения
        old_facts_map = ProfileIndexer.index_facts(old_facts)
        new_facts_map = ProfileIndexer.index_facts(new_facts)
        
        changes: List[Change] = []
        now = datetime.now()

        # 2. Сравнение Summary
        summary_diff = self._diff_summary(old.summary, new.summary, changes, now)
        
        # 3. Сравнение Engines (извлекаем из фактов или профиля, если есть)
        # Для упрощения берем уникальные engine из фактов
        old_engines = set(f["engine"] for f in old_facts_map.values())
        new_engines = set(f["engine"] for f in new_facts_map.values())
        
        engine_diff = EngineDiff(
            added=list(new_engines - old_engines),
            removed=list(old_engines - new_engines)
        )
        for eng in engine_diff.added:
            changes.append(self._make_change(ChangeType.ADDED, "engine", eng, "NEW_FACTS", now, {"engine": eng}))
        for eng in engine_diff.removed:
            changes.append(self._make_change(ChangeType.REMOVED, "engine", eng, "DEVICE_REAPPEARED", now, {"engine": eng}))

        # 4. Сравнение Capabilities
        old_caps = ProfileIndexer.index_capabilities(old.capabilities)
        new_caps = ProfileIndexer.index_capabilities(new.capabilities)
        
        cap_added = [k for k, v in new_caps.items() if v and not old_caps.get(k, False)]
        cap_removed = [k for k, v in old_caps.items() if v and not new_caps.get(k, False)]
        
        capability_diff = CapabilityDiff(
            became_available=cap_added,
            became_unavailable=cap_removed,
            modified=[] # Можно расширить при наличии модифицируемых параметров capability
        )
        for cap in cap_added:
            changes.append(self._make_change(ChangeType.ADDED, "capability", cap, "NEW_FACTS", now, {"capability": cap}))
        for cap in cap_removed:
            changes.append(self._make_change(ChangeType.REMOVED, "capability", cap, "CONFIGURATION_CHANGE", now, {"capability": cap}))

        # 5. Сравнение Facts (O(n) через словари)
        all_fact_ids = set(old_facts_map.keys()) | set(new_facts_map.keys())
        for fact_id in all_fact_ids:
            old_fact = old_facts_map.get(fact_id)
            new_fact = new_facts_map.get(fact_id)
            
            if old_fact and not new_fact:
                changes.append(self._make_fact_change(ChangeType.REMOVED, old_fact, None, now))
            elif new_fact and not old_fact:
                changes.append(self._make_fact_change(ChangeType.ADDED, None, new_fact, now))
            elif old_fact and new_fact:
                # Проверка на обновление
                changed_fields = []
                old_vals, new_vals = {}, {}
                for key in set(old_fact.keys()) | set(new_fact.keys()):
                    if old_fact.get(key) != new_fact.get(key):
                        changed_fields.append(key)
                        old_vals[key] = old_fact.get(key)
                        new_vals[key] = new_fact.get(key)
                
                if changed_fields:
                    changes.append(self._make_fact_change(
                        ChangeType.UPDATED, old_fact, new_fact, now, changed_fields, old_vals, new_vals
                    ))

        # 6. Сборка ProfileDiff
        diff_id = str(uuid.uuid4()) # В продакшене можно использовать SHA256 хешей
        
        return ProfileDiff(
            identity_uuid=old.identity.device_uuid,
            diff_id=diff_id,
            created_at=now,
            summary=summary_diff,
            engine_diff=engine_diff,
            capability_diff=capability_diff,
            changes=changes
        )

    def _diff_summary(self, old_sum, new_sum, changes: List[Change], now: datetime) -> SummaryDiff:
        def make_metric(old_val, new_val, field_name: str):
            delta = (new_val - old_val) if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)) else None
            if old_val != new_val:
                changes.append(self._make_change(
                    ChangeType.UPDATED, "summary", field_name, "NEW_FACTS", now, 
                    {"old": old_val, "new": new_val, "delta": delta}
                ))
            return SummaryMetric(old=old_val, new=new_val, delta=delta)

        return SummaryDiff(
            history_depth=make_metric(old_sum.history_depth, new_sum.history_depth, "history_depth"),
            facts=make_metric(old_sum.facts, new_sum.facts, "facts"),
            sessions=make_metric(old_sum.sessions, new_sum.sessions, "sessions"),
            confidence=make_metric(old_sum.confidence, new_sum.confidence, "confidence"),
            last_seen=make_metric(
                old_sum.last_seen.isoformat() if old_sum.last_seen else None,
                new_sum.last_seen.isoformat() if new_sum.last_seen else None,
                "last_seen"
            )
        )

    def _make_change(self, ctype: ChangeType, category: str, engine_or_name: str, 
                     reason_str: str, now: datetime, payload: Any) -> Change:
        reason = getattr(ChangeReason, reason_str, ChangeReason.NEW_FACTS)
        return Change(
            change_id=str(uuid.uuid4()),
            type=ctype,
            severity=self.resolver.resolve(ctype, category),
            reason=reason,
            engine=engine_or_name,
            category=category,
            timestamp=now,
            payload=payload
        )

    def _make_fact_change(self, ctype: ChangeType, old_fact: dict, new_fact: dict, 
                          now: datetime, changed_fields: List[str] = None, 
                          old_vals: dict = None, new_vals: dict = None) -> Change:
        
        fact_ref = new_fact if new_fact else old_fact
        category = fact_ref["category"]
        engine = fact_ref["engine"]
        fact_id = fact_ref["id"]
        
        payload = FactChange(
            fact_uuid=fact_id,
            changed_fields=changed_fields or (list(new_fact.keys()) if ctype == ChangeType.ADDED else []),
            old_values=old_vals or (old_fact if ctype == ChangeType.REMOVED else {}),
            new_values=new_vals or (new_fact if ctype == ChangeType.ADDED else {})
        )
        
        reason = ChangeReason.NEW_FACTS if ctype == ChangeType.ADDED else ChangeReason.DEVICE_REAPPEARED if ctype == ChangeType.REMOVED else ChangeReason.CONFIGURATION_CHANGE
        
        return Change(
            change_id=str(uuid.uuid4()),
            type=ctype,
            severity=self.resolver.resolve(ctype, category),
            reason=reason,
            engine=engine,
            category=category,
            timestamp=now,
            payload=payload
        )
