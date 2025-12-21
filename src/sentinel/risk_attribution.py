"""
Risk Attribution Layer - Quantifies business impact of LLM failures
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class BusinessContext:
    """Business metrics context for risk calculation."""
    daily_users: int = 10000
    avg_session_value: float = 50.0
    recommendation_conversion_rate: float = 0.08
    avg_order_value: float = 65.0
    hourly_revenue: float = 20833.0
    refund_rate_on_poor_recs: float = 0.05


class RiskAttributionLayer:
    """Calculates business impact of LLM failures."""
    
    def __init__(self, context: BusinessContext):
        """Initialize with business context."""
        self.context = context
    
    def add_to_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Add risk attribution to incident."""
        
        failure_class = incident.get("failure_classification", {}).get("primary_class")
        failure_score = incident.get("failure_classification", {}).get("failure_score", 0)
        
        # Base calculation
        hourly_impact_percentage = failure_score * 0.5
        hourly_revenue_lost = self.context.hourly_revenue * hourly_impact_percentage
        
        # Estimate affected users
        affected_users = self.context.daily_users * (failure_score / 2)
        
        # Calculate 24-hour projection
        projected_24h_revenue_lost = hourly_revenue_lost * 24
        
        # Calculate refund costs
        potential_refund_cost = affected_users * self.context.avg_order_value * self.context.refund_rate_on_poor_recs
        
        # Total business impact
        total_impact = projected_24h_revenue_lost + potential_refund_cost
        
        # Risk attribution
        incident["risk_attribution"] = {
            "methodology": "Deterministic business impact quantification",
            "calculation": {
                "failure_score": failure_score,
                "hourly_impact_percentage": hourly_impact_percentage,
                "hourly_revenue_lost": round(hourly_revenue_lost, 2),
                "projected_24h_revenue_lost": round(projected_24h_revenue_lost, 2),
                "affected_users_estimate": int(affected_users),
                "potential_refund_cost": round(potential_refund_cost, 2),
                "total_impact_24h": round(total_impact, 2),
            },
            "severity": self._calculate_severity(failure_score),
            "confidence": incident.get("failure_classification", {}).get("confidence", 0),
        }
        
        return incident
    
    def _calculate_severity(self, failure_score: float) -> str:
        """Map failure score to severity level."""
        if failure_score < 0.3:
            return "LOW"
        elif failure_score < 0.6:
            return "MEDIUM"
        elif failure_score < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"