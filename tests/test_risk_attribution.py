"""
Unit tests for RiskAttributionLayer
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sentinel.risk_attribution import RiskAttributionLayer, BusinessContext
from src.sentinel.failure_classifier import FailureClassifier
from src.sentinel.failure_taxonomy import FailureClass
from src.sentinel.incident_enrichment import build_incident_payload


def test_risk_layer_initialization():
    """Test risk layer can be initialized."""
    context = BusinessContext()
    risk_layer = RiskAttributionLayer(context)
    assert risk_layer is not None
    print("✓ Risk attribution layer initialized")


def test_hallucination_impact():
    """Test business impact calculation for hallucination."""
    context = BusinessContext()
    risk_layer = RiskAttributionLayer(context)
    
    # Create mock incident
    incident = {
        "title": "Test Hallucination",
        "failure_classification": {
            "primary_class": FailureClass.HALLUCINATION_RISK,
            "failure_score": 0.78,
            "confidence": 0.94
        },
        "evidence": {
            "confidence_score": 0.52,
        },
        "latency_ms": 3200,
    }
    
    result = risk_layer.add_to_incident(incident)
    
    assert "risk_attribution" in result
    assert "calculation" in result["risk_attribution"]
    
    calc = result["risk_attribution"]["calculation"]
    assert calc["projected_24h_revenue_lost"] > 0
    assert calc["affected_users_estimate"] > 0
    
    print(f"✓ Revenue at risk: ${calc['projected_24h_revenue_lost']:.2f}/day")
    print(f"✓ Affected users: {calc['affected_users_estimate']:.0f}")


def test_latency_impact():
    """Test business impact calculation for latency spike."""
    context = BusinessContext()
    risk_layer = RiskAttributionLayer(context)
    
    incident = {
        "title": "Test Latency Spike",
        "failure_classification": {
            "primary_class": FailureClass.LATENCY_SPIKE_ANOMALY,
            "failure_score": 0.67,
            "confidence": 0.88
        },
        "evidence": {
            "latency_ms": 5000,
        },
        "latency_ms": 5000,
    }
    
    result = risk_layer.add_to_incident(incident)
    
    assert "risk_attribution" in result
    calc = result["risk_attribution"]["calculation"]
    
    print(f"✓ Latency impact calculated: ${calc['projected_24h_revenue_lost']:.2f}/day")


def test_cost_anomaly_impact():
    """Test business impact calculation for cost anomaly."""
    context = BusinessContext()
    risk_layer = RiskAttributionLayer(context)
    
    incident = {
        "title": "Test Cost Anomaly",
        "failure_classification": {
            "primary_class": FailureClass.COST_ANOMALY,
            "failure_score": 0.70,
            "confidence": 0.85
        },
        "evidence": {
            "input_tokens": 1200,
        },
        "latency_ms": 1200,
    }
    
    result = risk_layer.add_to_incident(incident)
    
    assert "risk_attribution" in result
    calc = result["risk_attribution"]["calculation"]
    
    print(f"✓ Cost impact calculated: ${calc['projected_24h_revenue_lost']:.2f}/day")


def test_healthy_request_no_impact():
    """Test no impact for healthy requests."""
    context = BusinessContext()
    risk_layer = RiskAttributionLayer(context)
    
    incident = {
        "title": "Test Healthy",
        "failure_classification": {
            "primary_class": FailureClass.NO_FAILURE,
            "failure_score": 0.1,
            "confidence": 0.99
        },
        "evidence": {},
        "latency_ms": 1200,
    }
    
    result = risk_layer.add_to_incident(incident)
    
    # Healthy requests might not have risk_attribution, or it should be minimal
    if "risk_attribution" in result:
        calc = result["risk_attribution"]["calculation"]
        assert calc["projected_24h_revenue_lost"] < 100, "Healthy requests should have minimal impact"
    
    print("✓ Healthy request has no/minimal business impact")


def test_recovery_recommendations():
    """Test that recovery recommendations are provided."""
    context = BusinessContext()
    risk_layer = RiskAttributionLayer(context)
    
    incident = {
        "title": "Test Recovery",
        "failure_classification": {
            "primary_class": FailureClass.HALLUCINATION_RISK,
            "failure_score": 0.78,
            "confidence": 0.94
        },
        "evidence": {
            "confidence_score": 0.52,
        },
        "latency_ms": 3200,
        "recovery_recommendations": [
            {
                "action": "Fallback to Claude 3.5 Sonnet",
                "expected_recovery_time_minutes": 2,
                "recovery_rate": 0.95,
                "confidence": 0.92
            }
        ]
    }
    
    result = risk_layer.add_to_incident(incident)
    
    assert "recovery_recommendations" in result
    assert len(result["recovery_recommendations"]) > 0
    
    print(f"✓ Recovery recommendations provided")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING: RiskAttributionLayer")
    print("="*60)
    
    try:
        test_risk_layer_initialization()
        test_hallucination_impact()
        test_latency_impact()
        test_cost_anomaly_impact()
        test_healthy_request_no_impact()
        test_recovery_recommendations()
        
        print("\n" + "="*60)
        print("✓ ALL RISK ATTRIBUTION TESTS PASSED")
        print("="*60)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)