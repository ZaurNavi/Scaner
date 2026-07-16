#!/usr/bin/env python3
from dataclasses import dataclass

@dataclass
class VersionSnapshot:
    identity: str = "1.0.0"; history: str = "1.0.0"; session: str = "1.0.0"
    timeline: str = "1.0.0"; provider: str = "1.0.0"; metric: str = "1.0.0"
    feature: str = "1.0.0"; rule: str = "1.0.0"; engine: str = "1.0.0"
    def to_cache_key(self) -> tuple:
        return (self.identity, self.history, self.session, self.timeline, self.provider, self.metric, self.feature, self.rule, self.engine)
