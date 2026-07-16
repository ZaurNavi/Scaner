#!/usr/bin/env python3
from dataclasses import dataclass

@dataclass
class Coverage:
    timeline_coverage: float = 0.0
    metric_coverage: float = 0.0
    feature_coverage: float = 0.0
    rule_coverage: float = 0.0
    fact_coverage: float = 0.0
    def to_dict(self) -> dict:
        return {"timeline": self.timeline_coverage, "metric": self.metric_coverage,
                "feature": self.feature_coverage, "rule": self.rule_coverage, "fact": self.fact_coverage}
