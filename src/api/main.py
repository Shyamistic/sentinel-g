from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time
import uuid
from datetime import datetime

from src.core.config import settings
from src.core.models import RecommendationRequest, RecommendationResponse
from src.llm.ecommerce_agent import EcommerceRecommendationAgent
from src.sentinel.failure_classifier import FailureClassifier
from src.sentinel.incident_enrichment import build_incident_payload, add_recovery_recommendations
from src.sentinel.risk_attribution import RiskAttributionLayer, BusinessContext

app = FastAPI(title="SENTINEL-G", version="1.0.0")

# Initialize components
agent = EcommerceRecommendationAgent()
classifier = FailureClassifier()
risk_layer = RiskAttributionLayer(BusinessContext())

# Telemetry
app_start_time = datetime.utcnow()


@app.get("/health")
async def health():
    """Health check endpoint."""
    uptime = (datetime.utcnow() - app_start_time).total_seconds()
    return {
        "status": "ok",
        "service": "sentinel-g",
        "version": "1.0.0",
        "uptime_seconds": uptime
    }


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check."""
    uptime = (datetime.utcnow() - app_start_time).total_seconds()
    return {
        "status": "ok",
        "service": "sentinel-g",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.datadog_env,
        "gcp_project": settings.gcp_project_id,
    }


@app.post("/recommend")
async def recommend(request: RecommendationRequest) -> RecommendationResponse:
    """Generate product recommendations with failure detection."""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        # Generate recommendations
        response = agent.recommend(request)
        response.request_id = request_id
        
        # Extract telemetry
        telemetry = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "model_version": "gemini-2.0-flash",
            "tokens_used": {"input": 150, "output": int(response.latency_ms / 10)},
            "latency_ms": response.latency_ms,
            "confidence_score": response.confidence_score,
            "diversity_score": response.recommendation_diversity,
            "recommendation_count": len(response.recommendations),
            "tool_calls": 0,
            "retry_depth": 0,
            "failure_signal": None,
            "predicted_ctr": response.recommendations[0].predicted_ctr if response.recommendations else 0.0,
        }
        
        # Classify failures
        classification = classifier.classify(telemetry)
        response.failure_class = classification.primary_class.value if classification.primary_class.value != "NO_FAILURE" else None
        response.failure_score = classification.failure_score if classification.failure_score > 0.5 else None
        
        # If failure detected, create incident
        if response.failure_class:
            incident = build_incident_payload(telemetry, classification)
            incident = add_recovery_recommendations(incident)
            incident = risk_layer.add_to_incident(incident)
            
            print(f"✓ Incident created: {incident['title']}")
            print(f"  Revenue at risk: ${incident.get('risk_attribution', {}).get('calculation', {}).get('projected_24h_revenue_lost', 0):.2f}")
        
        return response
    
    except Exception as e:
        print(f"❌ Error in /recommend: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.post("/test-failure")
async def test_failure(failure_type: str = "hallucination"):
    """Test endpoint to simulate failures (for demo)."""
    request_id = str(uuid.uuid4())
    
    # Simulate different failure types
    telemetry = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "model_version": "gemini-2.0-flash",
        "tokens_used": {"input": 150, "output": 200},
        "latency_ms": 1200,
        "confidence_score": 0.88,
        "diversity_score": 0.65,
        "recommendation_count": 5,
        "tool_calls": 0,
        "retry_depth": 0,
        "failure_signal": None,
        "predicted_ctr": 0.042,
    }
    
    # Override based on test type
    if failure_type == "hallucination":
        telemetry["confidence_score"] = 0.52
        telemetry["latency_ms"] = 3200
        telemetry["tokens_used"]["output"] = 320
    elif failure_type == "latency":
        telemetry["latency_ms"] = 5000
    elif failure_type == "cost":
        telemetry["tokens_used"]["input"] = 1200
    elif failure_type == "diversity":
        telemetry["diversity_score"] = 0.35
    
    # Classify
    classification = classifier.classify(telemetry)
    
    # Create incident
    incident = build_incident_payload(telemetry, classification)
    incident = add_recovery_recommendations(incident)
    incident = risk_layer.add_to_incident(incident)
    
    return {
        "request_id": request_id,
        "failure_type": failure_type,
        "classification": classification.primary_class.value,
        "failure_score": classification.failure_score,
        "incident": incident,
    }