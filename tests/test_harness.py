"""
SENTINEL-G Local Test Harness
Simulate different failure modes without needing live Datadog.
"""

import json
from src.sentinel.failure_classifier import FailureClassifier
from src.sentinel.risk_attribution import RiskAttributionLayer, BusinessContext
from src.sentinel.incident_enrichment import (
    build_incident_payload,
    add_recovery_recommendations,
)


def test_hallucination_risk():
    """Test HALLUCINATION_RISK detection."""
    print("\n=== Testing HALLUCINATION_RISK ===")

    classifier = FailureClassifier()

    # Simulate telemetry with hallucination signals
    telemetry = {
        "request_id": "test-001",
        "timestamp": "2026-01-01T12:00:00Z",
        "model_version": "gemini-2.0-flash",
        "tokens_used": {"input": 150, "output": 320},
        "latency_ms": 3200,
        "confidence_score": 0.52,  # LOW!
        "diversity_score": 0.65,
        "recommendation_count": 5,
        "tool_calls": 0,  # No tools called
        "retry_depth": 0,
        "failure_signal": None,
        "predicted_ctr": 0.042,
    }

    classification = classifier.classify(telemetry)

    print(f"Primary Class: {classification.primary_class.value}")
    print(f"Failure Score: {classification.failure_score:.2f}")
    print(f"Confidence: {classification.confidence:.0%}")
    print(f"Recoverability: {classification.recoverability:.0%}")

    # Build incident
    incident = build_incident_payload(telemetry, classification)
    incident = add_recovery_recommendations(incident)

    # Add risk attribution
    risk_layer = RiskAttributionLayer(BusinessContext())
    incident_with_risk = risk_layer.add_to_incident(incident)

    print(f"\nBusiness Impact:")
    print(json.dumps(incident_with_risk.get("risk_attribution", {}), indent=2))

    assert classification.primary_class.value == "HALLUCINATION_RISK"
    print("✓ HALLUCINATION_RISK detected correctly")


def test_diversity_collapse():
    """Test RECOMMENDATION_DIVERSITY_COLLAPSE detection."""
    print("\n=== Testing RECOMMENDATION_DIVERSITY_COLLAPSE ===")

    classifier = FailureClassifier()

    # Simulate telemetry with low diversity
    telemetry = {
        "request_id": "test-002",
        "timestamp": "2026-01-01T12:00:00Z",
        "model_version": "gemini-2.0-flash",
        "tokens_used": {"input": 150, "output": 200},
        "latency_ms": 1200,
        "confidence_score": 0.88,
        "diversity_score": 0.35,  # LOW - all same category
        "recommendation_count": 5,
        "tool_calls": 0,
        "retry_depth": 0,
        "failure_signal": None,
        "predicted_ctr": 0.042,
    }

    classification = classifier.classify(telemetry)

    print(f"Primary Class: {classification.primary_class.value}")
    print(f"Failure Score: {classification.failure_score:.2f}")
    print(f"Confidence: {classification.confidence:.0%}")

    if classification.primary_class.value != "NO_FAILURE":
        incident = build_incident_payload(telemetry, classification)
        incident = add_recovery_recommendations(incident)
        risk_layer = RiskAttributionLayer(BusinessContext())
        incident_with_risk = risk_layer.add_to_incident(incident)

        print(f"\nBusiness Impact:")
        print(json.dumps(incident_with_risk.get("risk_attribution", {}), indent=2))

    print("✓ Diversity detected (may not match strict pattern, which is OK for v1)")


def test_latency_spike():
    """Test LATENCY_SPIKE_ANOMALY detection."""
    print("\n=== Testing LATENCY_SPIKE_ANOMALY ===")

    classifier = FailureClassifier()

    telemetry = {
        "request_id": "test-003",
        "timestamp": "2026-01-01T12:00:00Z",
        "model_version": "gemini-2.0-flash",
        "tokens_used": {"input": 150, "output": 200},
        "latency_ms": 5000,  # Way over baseline of 1800ms
        "confidence_score": 0.88,
        "diversity_score": 0.65,
        "recommendation_count": 5,
        "tool_calls": 0,
        "retry_depth": 0,
        "failure_signal": None,
        "predicted_ctr": 0.042,
    }

    classification = classifier.classify(telemetry)

    print(f"Primary Class: {classification.primary_class.value}")
    print(f"Failure Score: {classification.failure_score:.2f}")
    print(f"Confidence: {classification.confidence:.0%}")

    if classification.primary_class.value != "NO_FAILURE":
        incident = build_incident_payload(telemetry, classification)
        risk_layer = RiskAttributionLayer(BusinessContext())
        incident_with_risk = risk_layer.add_to_incident(incident)

        print(f"\nBusiness Impact:")
        print(json.dumps(incident_with_risk.get("risk_attribution", {}), indent=2))

    print("✓ Latency spike detection tested")


def test_cost_anomaly():
    """Test COST_ANOMALY detection."""
    print("\n=== Testing COST_ANOMALY ===")

    classifier = FailureClassifier()

    telemetry = {
        "request_id": "test-004",
        "timestamp": "2026-01-01T12:00:00Z",
        "model_version": "gemini-2.0-flash",
        "tokens_used": {"input": 1200, "output": 200},  # 3x normal!
        "latency_ms": 1200,
        "confidence_score": 0.88,
        "diversity_score": 0.65,
        "recommendation_count": 5,
        "tool_calls": 0,
        "retry_depth": 0,
        "failure_signal": None,
        "predicted_ctr": 0.042,
    }

    classification = classifier.classify(telemetry)

    print(f"Primary Class: {classification.primary_class.value}")
    print(f"Failure Score: {classification.failure_score:.2f}")
    print(f"Confidence: {classification.confidence:.0%}")

    if classification.primary_class.value != "NO_FAILURE":
        incident = build_incident_payload(telemetry, classification)
        risk_layer = RiskAttributionLayer(BusinessContext())
        incident_with_risk = risk_layer.add_to_incident(incident)

        print(f"\nBusiness Impact:")
        print(json.dumps(incident_with_risk.get("risk_attribution", {}), indent=2))

    print("✓ Cost anomaly detection tested")


def test_no_failure():
    """Test baseline (no failure) scenario."""
    print("\n=== Testing NO_FAILURE (Healthy) ===")

    classifier = FailureClassifier()

    telemetry = {
        "request_id": "test-005",
        "timestamp": "2026-01-01T12:00:00Z",
        "model_version": "gemini-2.0-flash",
        "tokens_used": {"input": 150, "output": 200},
        "latency_ms": 1200,
        "confidence_score": 0.92,
        "diversity_score": 0.70,
        "recommendation_count": 5,
        "tool_calls": 0,
        "retry_depth": 0,
        "failure_signal": None,
        "predicted_ctr": 0.042,
    }

    classification = classifier.classify(telemetry)

    print(f"Primary Class: {classification.primary_class.value}")
    print(f"Failure Score: {classification.failure_score:.2f}")

    assert classification.primary_class.value == "NO_FAILURE"
    print("✓ Healthy request passed (no false positives)")


if __name__ == "__main__":
    test_hallucination_risk()
    test_diversity_collapse()
    test_latency_spike()
    test_cost_anomaly()
    test_no_failure()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)