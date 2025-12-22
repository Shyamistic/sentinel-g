from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import sys
import json
import requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# DATADOG EVENT INTEGRATION (REAL, NOT METRICS)
# ============================================================================

DATADOG_API_KEY = os.getenv("DATADOG_API_KEY")
DATADOG_APP_KEY = os.getenv("DATADOG_APP_KEY")
DATADOG_SITE = os.getenv("DATADOG_SITE", "datadoghq.com")

# ============================================================================
# DATADOG EVENT INTEGRATION (REAL, NOT METRICS)
# ============================================================================

DATADOG_API_KEY = os.getenv("DATADOG_API_KEY")
DATADOG_APP_KEY = os.getenv("DATADOG_APP_KEY")
DATADOG_SITE = os.getenv("DATADOG_SITE", "datadoghq.com")

# REPLACE THIS FUNCTION:
def send_datadog_event(title: str, text: str, tags: List[str]):
    """Send event to Datadog via REST API"""
    if not DATADOG_API_KEY or not DATADOG_APP_KEY:
        print(f"⚠ Datadog credentials not set. Skipping event.")
        return
    
    try:
        import requests
        
        url = f"https://api.datadoghq.com/api/v1/events"
        
        headers = {
            "DD-API-KEY": DATADOG_API_KEY,
            "Content-Type": "application/json",
        }
        
        payload = {
            "title": title,
            "text": text,
            "tags": tags,
            "source_type_name": "sentinel-g",
            "priority": "normal",
        }
        
        print(f"DEBUG: Sending to {url}")
        print(f"DEBUG: Payload: {payload}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response: {response.text}")
        
        if response.status_code == 202:
            print(f"✓ Datadog Event Created: {title}")
        else:
            print(f"⚠ Datadog event failed ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"⚠ Datadog event failed: {str(e)}")


app = FastAPI(title="SENTINEL-G API", version="1.0.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# FAILURE CLASSIFICATION
# ============================================================================

class FailureClass(str, Enum):
    HALLUCINATION_RISK = "HALLUCINATION_RISK"
    LATENCY_ANOMALY = "LATENCY_ANOMALY"
    COST_EXPLOSION = "COST_EXPLOSION"
    DIVERSITY_COLLAPSE = "DIVERSITY_COLLAPSE"
    RETRY_DEPTH_EXCEEDED = "RETRY_DEPTH_EXCEEDED"
    TOKEN_LIMIT_BREACH = "TOKEN_LIMIT_BREACH"
    CONFIDENCE_DRIFT = "CONFIDENCE_DRIFT"
    OUTPUT_VARIANCE = "OUTPUT_VARIANCE"
    TOOL_FAILURE = "TOOL_FAILURE"
    FREQUENCY_ANOMALY = "FREQUENCY_ANOMALY"


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

incidents_db: Dict[str, dict] = {}
resolved_incidents: List[dict] = []


# ============================================================================
# DETERMINISTIC FAILURE CLASSIFIER
# ============================================================================

def classify_failure(failure_type: str) -> Dict:
    """Classify failure deterministically"""
    
    classifications = {
        "hallucination": {
            "primary_class": FailureClass.HALLUCINATION_RISK,
            "confidence": 0.52,
            "latency_ms": 3200,
            "tokens_output": 320,
            "diversity": 0.45,
        },
        "latency": {
            "primary_class": FailureClass.LATENCY_ANOMALY,
            "confidence": 0.68,
            "latency_ms": 4500,
            "tokens_output": 220,
            "diversity": 0.70,
        },
        "cost": {
            "primary_class": FailureClass.COST_EXPLOSION,
            "confidence": 0.65,
            "latency_ms": 2800,
            "tokens_output": 520,
            "diversity": 0.65,
        },
    }
    
    return classifications.get(failure_type, classifications["hallucination"])


def build_failure_lineage(failure_type: str) -> List[Dict]:
    """Build temporal degradation story"""
    now = datetime.utcnow()
    return [
        {
            "timestamp": (now - timedelta(minutes=12)).isoformat(),
            "time_marker": "t-12m",
            "signal": "confidence_drift_begins",
            "value": 0.52,
            "description": "Confidence threshold approaching",
        },
        {
            "timestamp": (now - timedelta(minutes=6)).isoformat(),
            "time_marker": "t-6m",
            "signal": "token_spike",
            "value": 320.00,
            "description": "Output tokens increasing",
        },
        {
            "timestamp": (now - timedelta(minutes=2)).isoformat(),
            "time_marker": "t-2m",
            "signal": "latency_acceleration",
            "value": 3200.00,
            "description": "Response time degradation",
        },
        {
            "timestamp": now.isoformat(),
            "time_marker": "t+0m",
            "signal": "failure_triggered",
            "value": 0.78,
            "description": "HALLUCINATION_RISK detected",
        },
    ]


def calculate_business_impact(classification: Dict) -> Dict:
    """Calculate business impact deterministically"""
    
    base_hourly_revenue = 24333  # $583K/day
    hours_undetected = 8
    
    confidence = classification["confidence"]
    latency = classification["latency_ms"]
    
    severity = 1.0 - confidence
    if latency > 3000:
        severity = min(1.0, severity + 0.15)
    
    projected_24h_lost = base_hourly_revenue * hours_undetected * severity
    
    return {
        "base_hourly_revenue": base_hourly_revenue,
        "hours_until_detection": hours_undetected,
        "failure_severity": round(severity, 2),
        "calculation": {
            "projected_24h_revenue_lost": round(projected_24h_lost, 0),
            "conversion_loss": round(projected_24h_lost * 0.63, 0),
            "refund_costs": round(projected_24h_lost * 0.24, 0),
            "support_overhead": round(projected_24h_lost * 0.13, 0),
        },
    }


def generate_recovery_options(failure_class: str) -> List[Dict]:
    """Generate ranked recovery actions"""
    
    recovery_map = {
        FailureClass.HALLUCINATION_RISK: [
            {
                "rank": 1,
                "action": "Fallback to Claude 3.5 Sonnet for 30 minutes",
                "success_rate": 0.85,
                "execution_time_min": 2,
            },
            {
                "rank": 2,
                "action": "Add semantic validation layer",
                "success_rate": 0.70,
                "execution_time_min": 30,
            },
            {
                "rank": 3,
                "action": "Increase confidence threshold to 0.80",
                "success_rate": 0.65,
                "execution_time_min": 5,
            },
        ],
        FailureClass.COST_EXPLOSION: [
            {
                "rank": 1,
                "action": "Switch to Gemini 1.5 Flash (cheaper model)",
                "success_rate": 0.82,
                "execution_time_min": 3,
            },
            {
                "rank": 2,
                "action": "Enable prompt caching",
                "success_rate": 0.75,
                "execution_time_min": 15,
            },
            {
                "rank": 3,
                "action": "Reduce context window to 2K tokens",
                "success_rate": 0.60,
                "execution_time_min": 2,
            },
        ],
        FailureClass.LATENCY_ANOMALY: [
            {
                "rank": 1,
                "action": "Enable response streaming",
                "success_rate": 0.80,
                "execution_time_min": 5,
            },
            {
                "rank": 2,
                "action": "Switch to faster model variant",
                "success_rate": 0.72,
                "execution_time_min": 2,
            },
            {
                "rank": 3,
                "action": "Increase timeout threshold to 5s",
                "success_rate": 0.55,
                "execution_time_min": 1,
            },
        ],
    }
    
    return recovery_map.get(failure_class, recovery_map[FailureClass.HALLUCINATION_RISK])


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
def health():
    """Health check"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/test-failure")
def test_failure(failure_type: str = "hallucination"):
    """
    Simulate an LLM failure.
    Triggers Datadog event + local incident.
    """
    
    # Classify
    classification = classify_failure(failure_type)
    lineage = build_failure_lineage(failure_type)
    risk_attribution = calculate_business_impact(classification)
    recovery_options = generate_recovery_options(classification["primary_class"])
    
    # Build incident
    request_id = f"req-{int(time.time() * 1000)}"
    incident = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "failure_type": failure_type,
        "classification": {
            "primary_class": classification["primary_class"].value,
            "confidence": classification["confidence"],
            "latency_ms": classification["latency_ms"],
            "tokens_output": classification["tokens_output"],
            "diversity_score": classification["diversity"],
        },
        "failure_lineage": lineage,
        "risk_attribution": risk_attribution,
        "recovery_options": recovery_options,
        "status": "ALERT",
    }
    
    incidents_db[request_id] = incident
    
    # SEND DATADOG EVENT (THIS IS THE KEY)
    failure_class = classification["primary_class"].value
    impact_usd = int(risk_attribution["calculation"]["projected_24h_revenue_lost"])
    
    send_datadog_event(
        title=f"🔴 LLM Failure Detected: {failure_class}",
        text=f"""
**Failure Class:** {failure_class}
**Request ID:** {request_id}
**Confidence Score:** {classification['confidence']} (threshold: 0.70)
**Latency:** {classification['latency_ms']}ms (threshold: 2340ms)
**Diversity Score:** {classification['diversity']} (threshold: 0.50)

**Business Impact (24h):** ${impact_usd:,}
- Conversion Loss: ${int(risk_attribution['calculation']['conversion_loss']):,}
- Refund Costs: ${int(risk_attribution['calculation']['refund_costs']):,}
- Support Overhead: ${int(risk_attribution['calculation']['support_overhead']):,}

**Recommended Actions:**
1. {recovery_options[0]['action']} ({recovery_options[0]['success_rate']*100:.0f}% success)
2. {recovery_options[1]['action']} ({recovery_options[1]['success_rate']*100:.0f}% success)
3. {recovery_options[2]['action']} ({recovery_options[2]['success_rate']*100:.0f}% success)
""",
        tags=[
            "service:sentinel-g",
            "env:dev",
            f"failure:{failure_class.lower()}",
            f"impact:high",
            f"confidence:{classification['confidence']}",
            f"latency:{classification['latency_ms']}",
        ],
    )
    
    print(f"\n✓ Failure simulated: {failure_type.upper()}")
    print(f"  Request ID: {request_id}")
    print(f"  Datadog event triggered")
    print(f"  Business Impact: ${impact_usd:,}")
    
    return incident


@app.post("/apply-fix")
def apply_fix(request_id: str, action: str):
    """Apply recovery action"""
    
    if request_id not in incidents_db:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident = incidents_db[request_id]
    
    execution_time = random.randint(2, 15)
    
    # Send RECOVERY event to Datadog
    send_datadog_event(
        title=f"✓ LLM Recovery Applied: {action}",
        text=f"""
**Recovery Action:** {action}
**Request ID:** {request_id}
**Execution Time:** {execution_time} seconds

**Recovered Metrics:**
- Confidence: 0.92 (restored)
- Latency: 1500ms (normalized)
- Status: HEALTHY

System returned to operational state.
""",
        tags=[
            "service:sentinel-g",
            "env:dev",
            "status:recovery",
            f"action:{action.lower()}",
        ],
    )
    
    incident["status"] = "HEALTHY"
    incident["recovery_applied"] = {
        "action": action,
        "applied_at": datetime.utcnow().isoformat(),
        "execution_time_sec": execution_time,
    }
    
    resolved_incidents.append(incident)
    del incidents_db[request_id]
    
    print(f"\n✓ Recovery applied: {action}")
    print(f"  Datadog recovery event triggered")
    
    return {
        "request_id": request_id,
        "status": "HEALTHY",
        "recovery_action": action,
        "execution_time_sec": execution_time,
        "confidence_recovered": 0.92,
        "latency_normalized_ms": 1500,
    }


@app.get("/incidents")
def list_incidents():
    """Get all incidents"""
    return {
        "active": list(incidents_db.values()),
        "resolved": resolved_incidents,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
