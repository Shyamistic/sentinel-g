"""
Telemetry & Early Warning Signals
Surfaces pre-failure degradation without claiming prediction.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime
from collections import deque


@dataclass
class EarlyWarningSignal:
    """Individual early warning indicator."""
    name: str
    current_value: float
    threshold: float
    trend: str  # "stable", "degrading", "critical"
    triggered: bool
    timestamp: str


@dataclass
class FailureLineage:
    """Timeline of degradation leading to failure."""
    request_id: str
    failure_class: str
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_event(self, offset_minutes: int, event_type: str, value: float, reason: str):
        """Add event to lineage timeline."""
        self.timeline.append({
            "offset_minutes": offset_minutes,
            "event_type": event_type,
            "value": value,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def to_markdown(self) -> str:
        """Convert to readable markdown."""
        md = f"## Failure Lineage: {self.failure_class}\n\n"
        for event in sorted(self.timeline, key=lambda x: x['offset_minutes']):
            offset = event['offset_minutes']
            t = f"t-{abs(offset)}m" if offset < 0 else f"t+{offset}m"
            md += f"**{t}**: {event['event_type']} = {event['value']:.2f} ({event['reason']})\n"
        return md


class EarlyWarningDetector:
    """Detects early warning signals before user-visible failures."""
    
    def __init__(self, window_size: int = 100):
        """Initialize detector with rolling window."""
        self.window_size = window_size
        self.confidence_history = deque(maxlen=window_size)
        self.token_history = deque(maxlen=window_size)
        self.latency_history = deque(maxlen=window_size)
        self.diversity_history = deque(maxlen=window_size)
    
    def add_telemetry(self, telemetry: Dict[str, Any]):
        """Add telemetry point to rolling window."""
        self.confidence_history.append(telemetry.get("confidence_score", 0.9))
        self.token_history.append(telemetry.get("tokens_used", {}).get("input", 150))
        self.latency_history.append(telemetry.get("latency_ms", 1200))
        self.diversity_history.append(telemetry.get("diversity_score", 0.7))
    
    def detect_early_warnings(self) -> List[EarlyWarningSignal]:
        """Detect degradation trends BEFORE failure threshold."""
        warnings = []
        
        # Signal 1: Confidence Drift
        if len(self.confidence_history) >= 10:
            recent = list(self.confidence_history)[-10:]
            trend = (recent[-1] - recent[0]) / recent[0]  # % change
            
            if trend < -0.15:  # >15% drop
                warnings.append(EarlyWarningSignal(
                    name="Confidence Drift",
                    current_value=recent[-1],
                    threshold=0.70,
                    trend="degrading",
                    triggered=recent[-1] < 0.75,
                    timestamp=datetime.utcnow().isoformat(),
                ))
        
        # Signal 2: Token Growth Rate
        if len(self.token_history) >= 10:
            recent = list(self.token_history)[-10:]
            avg_growth = (recent[-1] - recent[0]) / len(recent)
            
            if avg_growth > 30:  # >30 tokens/request increase
                warnings.append(EarlyWarningSignal(
                    name="Token Growth Acceleration",
                    current_value=recent[-1],
                    threshold=600,
                    trend="degrading",
                    triggered=recent[-1] > 400,
                    timestamp=datetime.utcnow().isoformat(),
                ))
        
        # Signal 3: Latency Acceleration
        if len(self.latency_history) >= 10:
            recent = list(self.latency_history)[-10:]
            accel = (recent[-1] - recent[-5]) / recent[-5] if recent[-5] > 0 else 0
            
            if accel > 0.30:  # >30% increase
                warnings.append(EarlyWarningSignal(
                    name="Latency Acceleration",
                    current_value=recent[-1],
                    threshold=2340,
                    trend="degrading",
                    triggered=recent[-1] > 2500,
                    timestamp=datetime.utcnow().isoformat(),
                ))
        
        # Signal 4: Diversity Variance
        if len(self.diversity_history) >= 10:
            recent = list(self.diversity_history)[-10:]
            variance = sum((x - sum(recent)/len(recent))**2 for x in recent) / len(recent)
            
            if variance > 0.05:  # High variance = instability
                warnings.append(EarlyWarningSignal(
                    name="Diversity Variance Spike",
                    current_value=variance,
                    threshold=0.03,
                    trend="degrading",
                    triggered=variance > 0.08,
                    timestamp=datetime.utcnow().isoformat(),
                ))
        
        return warnings


class BusinessImpactBreakdown:
    """Breaks down business impact into components."""
    
    @staticmethod
    def calculate_breakdown(incident: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate component breakdown of business impact."""
        
        total_impact = incident.get("risk_attribution", {}).get("calculation", {}).get("total_impact_24h", 0)
        failure_class = incident.get("failure_classification", {}).get("primary_class", "UNKNOWN")
        
        # Component percentages vary by failure type
        if failure_class == "HALLUCINATION_RISK":
            return {
                "conversion_loss": round(total_impact * 0.63, 2),  # Lost conversions
                "refund_cost": round(total_impact * 0.24, 2),     # Returns
                "support_overhead": round(total_impact * 0.13, 2), # CS costs
            }
        elif failure_class == "LATENCY_SPIKE_ANOMALY":
            return {
                "conversion_loss": round(total_impact * 0.75, 2),  # Abandoned carts
                "refund_cost": round(total_impact * 0.10, 2),
                "support_overhead": round(total_impact * 0.15, 2),
            }
        elif failure_class == "COST_ANOMALY":
            return {
                "conversion_loss": round(total_impact * 0.40, 2),
                "refund_cost": round(total_impact * 0.20, 2),
                "support_overhead": round(total_impact * 0.40, 2),
            }
        else:
            # Generic split
            return {
                "conversion_loss": round(total_impact * 0.50, 2),
                "refund_cost": round(total_impact * 0.30, 2),
                "support_overhead": round(total_impact * 0.20, 2),
            }