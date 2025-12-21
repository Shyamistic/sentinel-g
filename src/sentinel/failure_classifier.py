"""
SENTINEL-G Failure Classifier
Deterministic 8-class LLM failure classification system.
"""

from typing import List, Dict, Any
from src.sentinel.failure_taxonomy import FailureClass, Signal, FailureClassification


class FailureClassifier:
    """
    Classifies LLM failures into 8 deterministic classes.
    No ML. Pure logic. Explainable.
    """

    # Base failure scores from matrix (per class)
    BASE_SCORES = {
        FailureClass.HALLUCINATION_RISK: 0.78,
        FailureClass.TOOL_CALL_DEADLOCK: 0.72,
        FailureClass.CONTEXT_WINDOW_POLLUTION: 0.71,
        FailureClass.RESPONSE_CLASS_DRIFT: 0.78,
        FailureClass.TOOL_SCHEMA_MISMATCH: 0.70,
        FailureClass.LATENCY_SPIKE_ANOMALY: 0.67,
        FailureClass.SEMANTIC_CORRECTNESS_DEGRADATION: 0.77,
        FailureClass.COST_ANOMALY: 0.70,
        FailureClass.NO_FAILURE: 0.0,
    }

    RECOVERABILITY = {
        FailureClass.HALLUCINATION_RISK: 0.60,
        FailureClass.TOOL_CALL_DEADLOCK: 0.50,
        FailureClass.CONTEXT_WINDOW_POLLUTION: 0.70,
        FailureClass.RESPONSE_CLASS_DRIFT: 0.55,
        FailureClass.TOOL_SCHEMA_MISMATCH: 0.85,
        FailureClass.LATENCY_SPIKE_ANOMALY: 0.75,
        FailureClass.SEMANTIC_CORRECTNESS_DEGRADATION: 0.40,
        FailureClass.COST_ANOMALY: 0.80,
        FailureClass.NO_FAILURE: 1.0,
    }

    def __init__(self, baselines: Dict[str, float] = None):
        """
        baselines: dict of metric names to baseline values
        Used for anomaly detection.
        """
        self.baselines = baselines or {
            "latency_ms": 1800,
            "confidence_score": 0.88,
            "diversity_score": 0.65,
            "predicted_ctr": 0.042,
            "tokens_input": 400,
        }
        self.historical_responses = []  # For drift detection

    def classify(self, telemetry: Dict[str, Any]) -> FailureClassification:
        """
        Main entry point. Classify telemetry into a failure class.
        """
        signals = self._extract_signals(telemetry)

        # Check each class in priority order
        if self._matches_hallucination_risk(signals, telemetry):
            return self._build_classification(
                FailureClass.HALLUCINATION_RISK,
                signals,
                telemetry,
            )

        if self._matches_tool_call_deadlock(signals, telemetry):
            return self._build_classification(
                FailureClass.TOOL_CALL_DEADLOCK,
                signals,
                telemetry,
            )

        if self._matches_context_window_pollution(signals, telemetry):
            return self._build_classification(
                FailureClass.CONTEXT_WINDOW_POLLUTION,
                signals,
                telemetry,
            )

        if self._matches_response_class_drift(signals, telemetry):
            return self._build_classification(
                FailureClass.RESPONSE_CLASS_DRIFT,
                signals,
                telemetry,
            )

        if self._matches_tool_schema_mismatch(signals, telemetry):
            return self._build_classification(
                FailureClass.TOOL_SCHEMA_MISMATCH,
                signals,
                telemetry,
            )

        if self._matches_latency_spike_anomaly(signals, telemetry):
            return self._build_classification(
                FailureClass.LATENCY_SPIKE_ANOMALY,
                signals,
                telemetry,
            )

        if self._matches_semantic_correctness_degradation(signals, telemetry):
            return self._build_classification(
                FailureClass.SEMANTIC_CORRECTNESS_DEGRADATION,
                signals,
                telemetry,
            )

        if self._matches_cost_anomaly(signals, telemetry):
            return self._build_classification(
                FailureClass.COST_ANOMALY,
                signals,
                telemetry,
            )

        # No failure detected
        return FailureClassification(
            primary_class=FailureClass.NO_FAILURE,
            failure_score=0.0,
            confidence=1.0,
            recoverability=1.0,
            evidence=[],
        )

    def _extract_signals(self, telemetry: Dict[str, Any]) -> List[Signal]:
        """Extract key signals from telemetry."""
        signals = []

        # Signal 1: Confidence score
        confidence = telemetry.get("confidence_score", 0.88)
        signals.append(
            Signal(
                name="confidence_score",
                value=confidence,
                threshold=0.70,
                triggered=confidence < 0.70,
            )
        )

        # Signal 2: Response length (tokens output)
        tokens_output = telemetry.get("tokens_used", {}).get("output", 0)
        signals.append(
            Signal(
                name="response_length_tokens",
                value=tokens_output,
                threshold=200,
                triggered=tokens_output > 200,
            )
        )

        # Signal 3: Latency anomaly
        latency = telemetry.get("latency_ms", 0)
        latency_threshold = self.baselines.get("latency_ms", 1800)
        signals.append(
            Signal(
                name="latency_anomaly",
                value=latency,
                threshold=latency_threshold * 1.3,  # 30% above baseline
                triggered=latency > latency_threshold * 1.3,
            )
        )

        # Signal 4: Tool calls
        tool_calls = telemetry.get("tool_calls", 0)
        signals.append(
            Signal(
                name="tool_calls_made",
                value=tool_calls,
                threshold=0,
                triggered=tool_calls == 0,
            )
        )

        # Signal 5: Diversity score (e-commerce specific)
        diversity = telemetry.get("diversity_score", 0.65)
        signals.append(
            Signal(
                name="diversity_score",
                value=diversity,
                threshold=0.40,
                triggered=diversity < 0.40,
            )
        )

        # Signal 6: Predicted CTR (e-commerce specific)
        predicted_ctr = telemetry.get("predicted_ctr", 0.042)
        ctr_threshold = self.baselines.get("predicted_ctr", 0.042)
        signals.append(
            Signal(
                name="predicted_ctr",
                value=predicted_ctr,
                threshold=ctr_threshold * 0.5,  # 50% below baseline
                triggered=predicted_ctr < ctr_threshold * 0.5,
            )
        )

        # Signal 7: Retry depth
        retry_depth = telemetry.get("retry_depth", 0)
        signals.append(
            Signal(
                name="retry_depth",
                value=retry_depth,
                threshold=3,
                triggered=retry_depth >= 3,
            )
        )

        # Signal 8: Input tokens (cost anomaly)
        tokens_input = telemetry.get("tokens_used", {}).get("input", 0)
        input_baseline = self.baselines.get("tokens_input", 400)
        signals.append(
            Signal(
                name="input_tokens",
                value=tokens_input,
                threshold=input_baseline * 1.5,
                triggered=tokens_input > input_baseline * 1.5,
            )
        )

        return signals

    def _matches_hallucination_risk(self, signals: List[Signal], telemetry: Dict) -> bool:
        """
        Hallucination Risk:
        - confidence < 0.70
        - response_length > 200 tokens
        - latency > p75 baseline
        - no tools called
        """
        triggered_names = {s.name for s in signals if s.triggered}
        required = {
            "confidence_score",
            "response_length_tokens",
            "latency_anomaly",
            "tool_calls_made",
        }
        return required.issubset(triggered_names)

    def _matches_tool_call_deadlock(self, signals: List[Signal], telemetry: Dict) -> bool:
        """
        Tool Call Deadlock:
        - retry_depth >= 3
        - tool_calls made but low success
        - spending a lot of time retrying
        """
        retry_depth = telemetry.get("retry_depth", 0)
        tool_calls = telemetry.get("tool_calls", 0)
        latency = telemetry.get("latency_ms", 0)

        return retry_depth >= 3 and tool_calls > 0 and latency > 2000

    def _matches_context_window_pollution(self, signals: List[Signal], telemetry: Dict) -> bool:
        """
        Context Window Pollution:
        - input tokens > 1.5x average
        - latency increase > 1.3x
        - confidence drop detected
        """
        triggered_names = {s.name for s in signals if s.triggered}
        return "input_tokens" in triggered_names and "latency_anomaly" in triggered_names

    def _matches_response_class_drift(self, signals: List[Signal], telemetry: Dict) -> bool:
        """
        Response Class Drift:
        - Check if this request's confidence is notably lower than recent average
        - (Simplified: just check confidence is abnormally low)
        """
        confidence = telemetry.get("confidence_score", 0.88)
        # If historical avg was high and this is low, it's drift
        if self.historical_responses:
            avg_confidence = sum(h.get("confidence_score", 0.88) for h in self.historical_responses) / len(
                self.historical_responses
            )
            if avg_confidence > 0.85 and confidence < 0.65:
                return True
        return False

    def _matches_tool_schema_mismatch(self, signals: List[Signal], telemetry: Dict) -> bool:
        """
        Tool Schema Mismatch:
        - Telemetry includes error signal indicating schema issue
        (For hackathon: simplified—check if failure_signal contains 'schema')
        """
        failure_signal = telemetry.get("failure_signal", None)
        return failure_signal and "schema" in failure_signal.lower()

    def _matches_latency_spike_anomaly(self, signals: List[Signal], telemetry: Dict) -> bool:
        """
        Latency Spike Anomaly:
        - latency > p95 baseline
        - confidence improvement minimal
        """
        triggered_names = {s.name for s in signals if s.triggered}
        confidence = telemetry.get("confidence_score", 0.88)

        return "latency_anomaly" in triggered_names and confidence < 0.92

    def _matches_semantic_correctness_degradation(self, signals: List[Signal], telemetry: Dict) -> bool:
        """
        Semantic Correctness Degradation:
        - Response passes syntax but semantic validation might fail
        (For hackathon: simplified—check if failure_signal is semantic)
        """
        failure_signal = telemetry.get("failure_signal", None)
        return failure_signal and "semantic" in failure_signal.lower()

    def _matches_cost_anomaly(self, signals: List[Signal], telemetry: Dict) -> bool:
        """
        Cost Anomaly:
        - input tokens > 2x average for request type
        - output unchanged
        """
        triggered_names = {s.name for s in signals if s.triggered}
        return "input_tokens" in triggered_names

    def _build_classification(
        self,
        failure_class: FailureClass,
        signals: List[Signal],
        telemetry: Dict,
    ) -> FailureClassification:
        """Build and return a FailureClassification."""
        failure_score = self._compute_failure_score(failure_class, signals)
        confidence = self._compute_confidence(signals)
        recoverability = self.RECOVERABILITY.get(failure_class, 0.5)

        # Track in history for drift detection
        self.historical_responses.append(telemetry)
        if len(self.historical_responses) > 100:
            self.historical_responses.pop(0)

        return FailureClassification(
            primary_class=failure_class,
            failure_score=failure_score,
            confidence=confidence,
            recoverability=recoverability,
            evidence=signals,
        )

    def _compute_failure_score(self, failure_class: FailureClass, signals: List[Signal]) -> float:
        """
        Compute failure score based on:
        - Base score for class
        - Signal strength (how many triggered)
        """
        base_score = self.BASE_SCORES.get(failure_class, 0.5)
        triggered_count = len([s for s in signals if s.triggered])
        signal_strength = min(1.0, triggered_count / 4.0)  # normalize to 4 key signals

        # More signals = higher confidence in failure score
        adjusted_score = base_score * (0.8 + signal_strength * 0.2)
        return min(1.0, adjusted_score)

    def _compute_confidence(self, signals: List[Signal]) -> float:
        """
        Confidence = how sure are we this is the right classification.
        More signals triggered = higher confidence.
        """
        triggered_count = len([s for s in signals if s.triggered])
        base_confidence = 0.5
        evidence_boost = min(0.4, triggered_count * 0.1)
        return min(1.0, base_confidence + evidence_boost)