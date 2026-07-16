#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
from enum import Enum

class EventType(Enum):
    CONNECTED = "connected"; DISCONNECTED = "disconnected"; AP_CHANGED = "ap_changed"
    SSID_CHANGED = "ssid_changed"; IP_CHANGED = "ip_changed"; LEASE_RENEWED = "lease_renewed"
    TRAFFIC_SAMPLE = "traffic_sample"; TRAFFIC_SPIKE = "traffic_spike"
    RSSI_CHANGED = "rssi_changed"; SIGNAL_CHANGED = "signal_changed"
    STATE_CHANGED = "state_changed"; AUTHENTICATED = "authenticated"; DEAUTHENTICATED = "deauthenticated"
    SESSION_STARTED = "session_started"; SESSION_ENDED = "session_ended"
    FIRST_SEEN = "first_seen"; LAST_SEEN = "last_seen"
    AGGREGATED_SESSION = "aggregated_session"; DAILY_WINDOW = "daily_window"; HOURLY_WINDOW = "hourly_window"

@dataclass
class TimelineEvent:
    id: str
    timestamp: datetime
    device_id: str
    event_type: EventType
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    quality: float = 0.9
    confidence: float = 90.0
    version: str = "1.0.0"

@dataclass
class Timeline:
    events: List[TimelineEvent] = field(default_factory=list)
    device_id: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    def is_immutable(self) -> bool: return True
    def get_by_type(self, event_type: EventType) -> List[TimelineEvent]:
        return [e for e in self.events if e.event_type == event_type]
    def count_by_type(self, event_type: EventType) -> int:
        return len(self.get_by_type(event_type))
