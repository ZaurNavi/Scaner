#!/usr/bin/env python3
"""Timeline Builder: строит Traffic Timeline из сырых событий."""
from datetime import datetime
from typing import List
from ..models import Timeline, TimelineEvent, TrafficEvent
from ..categories import EventType

class TimelineBuilder:
    """Строит Timeline из сырых TrafficEvent."""
    
    def build(self, traffic_events: List[TrafficEvent]) -> Timeline:
        """Преобразует сырые события в Timeline."""
        timeline_events = []
        
        for event in traffic_events:
            timeline_event = TimelineEvent(
                timestamp=event.timestamp,
                event_type=EventType.TRAFFIC_SAMPLE,
                payload={
                    "download_bytes": event.download_bytes,
                    "upload_bytes": event.upload_bytes,
                    "flow_count": event.flow_count,
                    "session_id": event.session_id
                },
                confidence=90.0,  # 0..100
                sources=[event.source],
                version="1.0.0"
            )
            timeline_events.append(timeline_event)
        
        timeline_events.sort(key=lambda e: e.timestamp)
        
        return Timeline(events=timeline_events)
