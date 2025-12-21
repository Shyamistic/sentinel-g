"""
SENTINEL-G Incident Enrichment
Builds rich incident payloads for Datadog with full context.
"""

from typing import Dict, Any, List
from datetime import datetime
from src.sentinel.failure_taxonomy import FailureClassification


def build_incident_payload(
    telemetry: Dict[str, Any],
    classification: FailureClassification,
) -> Dict[str, Any]:
    """
    Build a rich incident payload from telemetry + classification.
    This is what gets sent to Datadog Incidents API.
    """

    request_id = telemetry.get("request_id", "unknown")
    failure_class = classification.primary_class.value
    failure_score = classification.failure_score
    confidence = classification.confidence

    # Determine severity
    if failure_score > 0.75:
        severity = "HIGH"
    elif failure_score > 0.65:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # Build title
    title = (
        f"{failure_class} "
        f"(score: {failure_score:.2f}, confidence: {confidence:.0%})"
    )

    # Build evidence string
    evidence_lines = []
    for signal in classification.evidence:
        if signal.triggered:
            evidence_lines.append(
                f"  • {signal.name}: {signal.value:.2f} (threshold: {signal.threshold:.2f}) ✓"
            )

    evidence_str = "\n".join(evidence_lines) if evidence_lines else "No triggered signals (baseline)"

    # Build description
    description = f"""
**Failure Classification:** {failure_class}
**Failure Score:** {failure_score:.2f} / 1.00
**Classification Confidence:** {confidence:.0%}
**Recoverability:** {classification.recoverability:.0%}

**Evidence Signals (triggered):**
{evidence_str}

**Telemetry Summary:**
  • Request ID: {request_id}
  • Timestamp: {telemetry.get('timestamp', 'N/A')}
  • Model: {telemetry.get('model_version', 'N/A')}
  • Latency: {telemetry.get('latency_ms', 'N/A'):.0f}ms
  • Confidence Score: {telemetry.get('confidence_score', 'N/A'):.2f}
  • Diversity Score: {telemetry.get('diversity_score', 'N/A'):.2f}
  • Predicted CTR: {telemetry.get('predicted_ctr', 'N/A'):.4f}
  • Tokens Used: {telemetry.get('tokens_used', {})}

**Taxonomy Reference:**
See full taxonomy at: https://docs.sentinel-g.io/taxonomy#{failure_class.lower()}
"""

    incident = {
        "title": title,
        "severity": severity,
        "description": description,
        "tags": [
            f"failure_class:{failure_class}",
            f"failure_score:{failure_score:.2f}",
            f"confidence:{confidence:.0%}",
            f"request_id:{request_id}",
            "sentinel-g",
        ],
        "failure_classification": {
            "primary_class": failure_class,
            "failure_score": failure_score,
            "confidence": confidence,
            "recoverability": classification.recoverability,
        },
        "evidence": {signal.name: signal.value for signal in classification.evidence},
        "telemetry": telemetry,
    }

    return incident


def add_recovery_recommendations(incident: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add suggested recovery actions to incident based on failure class.
    """
    failure_class = incident.get("failure_classification", {}).get("primary_class", "UNKNOWN")

    recommendations = {
        "HALLUCINATION_RISK": [
            {
                "action": "Fallback to Claude 3.5 Sonnet for 30 minutes",
                "risk_level": "LOW",
                "recovery_confidence": 0.85,
                "rationale": "Claude excels at factual accuracy; gives time for investigation",
                "execution_time_minutes": 2,
            },
            {
                "action": "Add semantic validation checkpoint",
                "risk_level": "MEDIUM",
                "recovery_confidence": 0.70,
                "rationale": "Verify LLM output against known-good data before returning",
                "execution_time_minutes": 30,
            },
            {
                "action": "Increase confidence threshold for production",
                "risk_level": "LOW",
                "recovery_confidence": 0.65,
                "rationale": "Only return recommendations with confidence > 0.80",
                "execution_time_minutes": 5,
            },
        ],
        "RECOMMENDATION_DIVERSITY_COLLAPSE": [
            {
                "action": "Revert to previous model version",
                "risk_level": "LOW",
                "recovery_confidence": 0.95,
                "rationale": "Previous version had better diversity; quick rollback",
                "execution_time_minutes": 2,
            },
            {
                "action": "Enforce diversity constraint in prompt",
                "risk_level": "LOW",
                "recovery_confidence": 0.80,
                "rationale": "Add system instruction: 'Recommend from at least 3 categories'",
                "execution_time_minutes": 10,
            },
        ],
        "LATENCY_SPIKE_ANOMALY": [
            {
                "action": "Route to cached results (bypass model)",
                "risk_level": "LOW",
                "recovery_confidence": 0.90,
                "rationale": "Serve recommendations from cache while investigating",
                "execution_time_minutes": 1,
            },
            {
                "action": "Scale up Vertex AI quota",
                "risk_level": "LOW",
                "recovery_confidence": 0.85,
                "rationale": "Latency indicates rate-limiting; increase quota",
                "execution_time_minutes": 5,
            },
        ],
        "COST_ANOMALY": [
            {
                "action": "Audit system prompt for redundancy",
                "risk_level": "LOW",
                "recovery_confidence": 0.75,
                "rationale": "Check for token-inefficient instructions",
                "execution_time_minutes": 20,
            },
            {
                "action": "Switch to Gemini 1.5 Flash (cheaper model)",
                "risk_level": "MEDIUM",
                "recovery_confidence": 0.65,
                "rationale": "Lower cost; may have slight quality tradeoff",
                "execution_time_minutes": 15,
            },
        ],
        "PREDICTED_CTR_ANOMALY": [
            {
                "action": "Review category mix in training data",
                "risk_level": "MEDIUM",
                "recovery_confidence": 0.60,
                "rationale": "Seasonal or trend shift may require retraining",
                "execution_time_minutes": 45,
            },
            {
                "action": "A/B test with previous model",
                "risk_level": "LOW",
                "recovery_confidence": 0.80,
                "rationale": "Side-by-side comparison shows which performs better",
                "execution_time_minutes": 30,
            },
        ],
    }

    default_recommendations = [
        {
            "action": "Escalate to on-call engineer",
            "risk_level": "LOW",
            "recovery_confidence": 0.50,
            "rationale": "Failure class requires manual investigation",
            "execution_time_minutes": 15,
        },
    ]

    incident["recommended_actions"] = recommendations.get(failure_class, default_recommendations)
    return incident


def format_incident_for_datadog(incident: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format incident into Datadog Incidents API schema.
    """
    return {
        "title": incident.get("title", "Sentinel-G Incident"),
        "severity": incident.get("severity", "MEDIUM"),
        "description": incident.get("description", "No description provided"),
        "tags": incident.get("tags", []),
        "notify_on_create": True,
    }


def incident_to_markdown(incident: Dict[str, Any]) -> str:
    """
    Convert incident to readable markdown (for logging/debugging).
    """
    md = f"""# {incident.get('title', 'Incident')}

**Severity:** {incident.get('severity', 'UNKNOWN')}

{incident.get('description', 'No description')}

## Recommended Actions

"""
    for action in incident.get("recommended_actions", []):
        md += f"""
### {action.get('action', 'Unknown action')}

- **Risk Level:** {action.get('risk_level', 'UNKNOWN')}
- **Recovery Confidence:** {action.get('recovery_confidence', 0):.0%}
- **Execution Time:** {action.get('execution_time_minutes', 'N/A')} minutes
- **Rationale:** {action.get('rationale', 'N/A')}

"""
    return md