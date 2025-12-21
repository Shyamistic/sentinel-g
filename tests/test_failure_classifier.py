"""
Unit tests for FailureClassifier
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sentinel.failure_classifier import FailureClassifier
from src.sentinel.failure_taxonomy import FailureClass


def test_classifier_initialization():
    """Test classifier can be initialized."""
    classifier = FailureClassifier()
    assert classifier is not None
    print("✓ Classifier initialized successfully")


def test_hallucination_detection():
    """Test HALLUCINATION_RISK detection."""
    classifier = FailureClassifier()
    
    telemetry = {
        "request_id": "test-halluc-001",
        "timestamp": "2026-01-01T12:00:00Z",
        "model_version": "gemini-2.0-flash",
        "tokens_used": {"input": 150, "output": 320},
        "latency_ms": 3200,
        "confidence_score": 0.52,  # LOW
        "diversity_score": 0.65,
        "recommendation_count": 5,
        "tool_calls": 0,
        "retry_depth": 0,
        "failure_signal": None,
        "predicted_ctr": 0.042,
    }
    
    classification = classifier.classify(telemetry)
    
    assert classification.primary_class == FailureClass.HALLUCINATION_RISK
    assert classification.failure_score > 0.7
    print(f"✓ Hallucination detected: score={classification.failure_score:.2f}")


def test_latency_spike_detection():
    """Test LATENCY_SPIKE_ANOMALY detection."""
    classifier = FailureClassifier()
    
    telemetry = {
        "request_id": "test-latency-001",
        "timestamp": "2026-01-01T12:00:00Z",
        "model_version": "gemini-2.0-flash",
        "tokens_used": {"input": 150, "output": 200},
        "latency_ms": 5000,  # SPIKE
        "confidence_score": 0.88,
        "diversity_score": 0.65,
        "recommendation_count": 5,
        "tool_calls": 0,
        "retry_depth": 0,
        "failure_signal": None,
        "predicted_ctr": 0.042,
    }
    
    classification = classifier.classify(telemetry)
    
    assert classification.primary_class == FailureClass.LATENCY_SPIKE_ANOMALY
    print(f"✓ Latency spike detected: score={classification.failure_score:.2f}")


def test_cost_anomaly_detection():
    """Test COST_ANOMALY detection."""
    classifier = FailureClassifier()
    
    telemetry = {
        "request_id": "test-cost-001",
        "timestamp": "2026-01-01T12:00:00Z",
        "model_version": "gemini-2.0-flash",
        "tokens_used": {"input": 1200, "output": 200},  # 3x normal
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
    
    assert classification.primary_class == FailureClass.COST_ANOMALY
    print(f"✓ Cost anomaly detected: score={classification.failure_score:.2f}")


def test_healthy_request():
    """Test NO_FAILURE for healthy request."""
    classifier = FailureClassifier()
    
    telemetry = {
        "request_id": "test-healthy-001",
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
    
    assert classification.primary_class == FailureClass.NO_FAILURE
    assert classification.failure_score < 0.5
    print(f"✓ Healthy request passed: score={classification.failure_score:.2f}")


def test_diversity_collapse():
    """Test RECOMMENDATION_DIVERSITY_COLLAPSE detection."""
    classifier = FailureClassifier()
    
    telemetry = {
        "request_id": "test-diversity-001",
        "timestamp": "2026-01-01T12:00:00Z",
        "model_version": "gemini-2.0-flash",
        "tokens_used": {"input": 150, "output": 200},
        "latency_ms": 1200,
        "confidence_score": 0.88,
        "diversity_score": 0.35,  # COLLAPSED
        "recommendation_count": 5,
        "tool_calls": 0,
        "retry_depth": 0,
        "failure_signal": None,
        "predicted_ctr": 0.018,
    }
    
    classification = classifier.classify(telemetry)
    
    assert classification.primary_class in [
        FailureClass.RECOMMENDATION_DIVERSITY_COLLAPSE,
        FailureClass.RESPONSE_CLASS_DRIFT
    ]
    print(f"✓ Diversity collapse detected: {classification.primary_class.value}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING: FailureClassifier")
    print("="*60)
    
    try:
        test_classifier_initialization()
        test_hallucination_detection()
        test_latency_spike_detection()
        test_cost_anomaly_detection()
        test_diversity_collapse()
        test_healthy_request()
        
        print("\n" + "="*60)
        print("✓ ALL CLASSIFIER TESTS PASSED")
        print("="*60)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)