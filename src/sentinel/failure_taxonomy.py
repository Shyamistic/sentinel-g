from enum import Enum
from dataclasses import dataclass
from typing import List


class FailureClass(Enum):
    HALLUCINATION_RISK = "HALLUCINATION_RISK"
    TOOL_CALL_DEADLOCK = "TOOL_CALL_DEADLOCK"
    CONTEXT_WINDOW_POLLUTION = "CONTEXT_WINDOW_POLLUTION"
    RESPONSE_CLASS_DRIFT = "RESPONSE_CLASS_DRIFT"
    TOOL_SCHEMA_MISMATCH = "TOOL_SCHEMA_MISMATCH"
    LATENCY_SPIKE_ANOMALY = "LATENCY_SPIKE_ANOMALY"
    SEMANTIC_CORRECTNESS_DEGRADATION = "SEMANTIC_CORRECTNESS_DEGRADATION"
    COST_ANOMALY = "COST_ANOMALY"
    NO_FAILURE = "NO_FAILURE"


@dataclass
class Signal:
    name: str
    value: float
    threshold: float
    triggered: bool


@dataclass
class FailureClassification:
    primary_class: FailureClass
    failure_score: float
    confidence: float
    recoverability: float
    evidence: List[Signal]
