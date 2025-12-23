import time
import random
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# ============================================================================
# 1. ENTERPRISE SETUP & LOGGING (Screenshot 1840 Style)
# ============================================================================

load_dotenv()

# Configure structured JSON logging for Datadog
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "sentinel-g-api",
            "message": record.getMessage(),
            "module": record.module,
        }
        if hasattr(record, "props"):
            log_obj.update(record.props)
        return json.dumps(log_obj)

logger = logging.getLogger("sentinel-g")
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Datadog Initialization
DATADOG_API_KEY = os.getenv("DATADOG_API_KEY")
DATADOG_APP_KEY = os.getenv("DATADOG_APP_KEY")
DATADOG_AVAILABLE = False

if DATADOG_API_KEY:
    try:
        from datadog import initialize, api
        initialize(api_key=DATADOG_API_KEY, app_key=DATADOG_APP_KEY)
        DATADOG_AVAILABLE = True
        logger.info("Datadog Agent Connected", extra={"props": {"status": "connected"}})
    except Exception as e:
        logger.warning(f"Datadog init failed: {e}")

# ============================================================================
# 2. DATA MODELS (Research Grade)
# ============================================================================

class LLMModel(str, Enum):
    # Google First (Hackathon Rule)
    GEMINI_1_5_PRO = "gemini_1_5_pro"
    GEMINI_1_5_FLASH = "gemini_1_5_flash"
    GPT4 = "gpt4"
    GPT4O = "gpt4o"
    CLAUDE3_OPUS = "claude3_opus"

class FailureClass(str, Enum):
    # Standard
    HALLUCINATION_RISK = "HALLUCINATION_RISK"
    LATENCY_ANOMALY = "LATENCY_ANOMALY"
    COST_EXPLOSION = "COST_EXPLOSION"
    # Research Grade Additions
    PROMPT_INJECTION = "PROMPT_INJECTION_ATTEMPT"  # Security
    RAG_FAITHFULNESS_DROP = "RAG_FAITHFULNESS_DROP" # Context Adherence
    MODEL_COLLAPSE = "MODEL_COLLAPSE_ENTROPY"      # Diversity
    TONAL_DRIFT = "TONAL_DRIFT_HOSTILE"            # Safety

class CostRequest(BaseModel):
    current_model: str
    recommended_model: str
    monthly_requests: int

# ============================================================================
# 3. CORE LOGIC ENGINE
# ============================================================================

MODEL_SPECS = {
    "gemini_1_5_pro": {"name": "Gemini 1.5 Pro", "cost": 0.00125, "latency": 2000, "confidence": 0.70},
    "gemini_1_5_flash": {"name": "Gemini 1.5 Flash", "cost": 0.000375, "latency": 800, "confidence": 0.68},
    "gpt4": {"name": "GPT-4", "cost": 0.03, "latency": 2340, "confidence": 0.70},
    "gpt4o": {"name": "GPT-4o", "cost": 0.015, "latency": 1200, "confidence": 0.72},
}

# In-Memory DB
incidents_db = {}
resolved_incidents = []

def emit_metric(name: str, value: float, tags: List[str]):
    """Sends quantitative metrics to Datadog for Graphs"""
    if DATADOG_AVAILABLE:
        try:
            api.Metric.send(metric=name, points=value, tags=tags, type="gauge")
        except Exception:
            pass

def build_lineage(failure_type: str) -> List[Dict]:
    """Generates the 'T-12m' timeline data for the React Component"""
    now = datetime.utcnow()
    
    if failure_type == "hallucination":
        return [
            {"time_marker": "t-12m", "signal": "rag_context_drift", "value": 0.82, "description": "Vector similarity dropping", "timestamp": (now - timedelta(minutes=12)).isoformat()},
            {"time_marker": "t-6m", "signal": "uncertainty_spike", "value": 0.65, "description": "Logprobs variance increasing", "timestamp": (now - timedelta(minutes=6)).isoformat()},
            {"time_marker": "t-2m", "signal": "citation_missing", "value": 1.0, "description": "Output missing source refs", "timestamp": (now - timedelta(minutes=2)).isoformat()},
            {"time_marker": "t+0m", "signal": "failure_triggered", "value": 0.52, "description": "HALLUCINATION_RISK Detected", "timestamp": now.isoformat()},
        ]
    elif failure_type == "injection":
        return [
             {"time_marker": "t-1s", "signal": "heuristic_match", "value": 0.99, "description": "Pattern 'Ignore Instructions' found", "timestamp": now.isoformat()},
             {"time_marker": "t+0m", "signal": "firewall_block", "value": 1.0, "description": "PROMPT_INJECTION Blocked", "timestamp": now.isoformat()},
        ]
    # Default generic timeline
    return [
        {"time_marker": "t-5m", "signal": "anomaly_detected", "value": 0.0, "description": "Baseline deviation", "timestamp": (now - timedelta(minutes=5)).isoformat()},
        {"time_marker": "t+0m", "signal": "failure_triggered", "value": 1.0, "description": f"{failure_type.upper()} Detected", "timestamp": now.isoformat()},
    ]

def calculate_impact(confidence: float, failure_type: str) -> Dict:
    """Calculates the Financial Risk (The 'BusinessImpact.jsx' data)"""
    base_revenue = 24333 # Hourly
    severity = max(0.2, 1 - confidence)
    
    if failure_type == "injection":
        severity = 1.0 # Security risks are max severity
        
    loss = base_revenue * 8 * severity # 8 hours exposure
    
    return {
        "base_hourly_revenue": base_revenue,
        "hours_until_detection": 8,
        "failure_severity": round(severity * 100, 1),
        "calculation": {
            "projected_24h_revenue_lost": int(loss),
            "conversion_loss": int(loss * 0.63),
            "refund_costs": int(loss * 0.24),
            "support_overhead": int(loss * 0.13)
        }
    }

def get_recovery_options(failure_class: str) -> List[Dict]:
    """Returns ranked actions for 'RecoveryActions.jsx'"""
    if failure_class == FailureClass.HALLUCINATION_RISK:
        return [
            {"rank": 1, "action": "Enable Vertex AI Grounding", "success_rate": 0.94, "execution_time_min": 1, "roi": "High"},
            {"rank": 2, "action": "Switch to Gemini 1.5 Pro (High Reasoning)", "success_rate": 0.88, "execution_time_min": 2, "roi": "Medium"},
            {"rank": 3, "action": "Inject Self-Correction Prompt", "success_rate": 0.65, "execution_time_min": 5, "roi": "Low"}
        ]
    elif failure_class == FailureClass.PROMPT_INJECTION:
        return [
            {"rank": 1, "action": "Block IP & Reset Context", "success_rate": 1.0, "execution_time_min": 0, "roi": "Critical"},
            {"rank": 2, "action": "Switch to Llama Guard (Safety Layer)", "success_rate": 0.95, "execution_time_min": 5, "roi": "High"}
        ]
    # Default
    return [
        {"rank": 1, "action": "Switch to Gemini 1.5 Flash", "success_rate": 0.92, "execution_time_min": 2, "roi": "High"},
        {"rank": 2, "action": "Enable Response Streaming", "success_rate": 0.80, "execution_time_min": 10, "roi": "Medium"}
    ]

# ============================================================================
# 4. API ENDPOINTS
# ============================================================================

app = FastAPI(title="SENTINEL-G", description="LLM Reliability Control Plane")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "operational", "datadog": DATADOG_AVAILABLE, "timestamp": datetime.utcnow().isoformat()}

@app.get("/models")
def list_models():
    return {"models": MODEL_SPECS}

@app.post("/test-failure")
def test_failure(failure_type: str = "hallucination", model: str = "gemini_1_5_pro"):
    """
    The Main Demo Endpoint.
    Simulates: Hallucination, Latency, Cost, Injection (New), Tonal Drift (New)
    """
    request_id = f"req-{int(time.time() * 1000)}"
    base = MODEL_SPECS.get(model, MODEL_SPECS["gemini_1_5_pro"])
    
    # 1. Classification Logic (The "Brain")
    if failure_type == "hallucination":
        cls = FailureClass.HALLUCINATION_RISK
        conf = 0.52
        lat = base["latency"]
    elif failure_type == "injection":
        cls = FailureClass.PROMPT_INJECTION
        conf = 0.10 # Extremely low trust
        lat = 150 # Fast rejection
    elif failure_type == "drift":
        cls = FailureClass.TONAL_DRIFT
        conf = 0.60
        lat = base["latency"]
    elif failure_type == "latency":
        cls = FailureClass.LATENCY_ANOMALY
        conf = 0.75
        lat = 4500
    else: # Default
        cls = FailureClass.HALLUCINATION_RISK
        conf = 0.52
        lat = base["latency"]

    # 2. Build Rich Data Objects
    impact = calculate_impact(conf, failure_type)
    lineage = build_lineage(failure_type)
    recovery = get_recovery_options(cls)
    
    # 3. Log to Datadog (Logs + Metrics)
    # This matches Screenshot 1840
    logger.error(
        f"🔴 LLM Failure Detected: {cls.value}",
        extra={"props": {
            "request_id": request_id,
            "model": model,
            "failure_type": failure_type,
            "confidence": conf,
            "business_impact": impact["calculation"]["projected_24h_revenue_lost"]
        }}
    )
    
    # Metrics for Graphs
    emit_metric("sentinel.ai.confidence", conf, [f"model:{model}", f"failure:{failure_type}"])
    emit_metric("sentinel.business.risk", impact["calculation"]["projected_24h_revenue_lost"], [f"model:{model}"])
    
    # 4. Construct Response (Matching React Prop Types)
    incident = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "model": model,
        "classification": {
            "primary_class": cls.value,
            "confidence": conf,
            "latency_ms": lat,
            "diversity_score": 0.45 if failure_type == "hallucination" else 0.8,
            "tokens_output": 320
        },
        "business_impact": impact,
        "failure_lineage": lineage,
        "recovery_options": recovery,
        "status": "ALERT",
        "golden_ratio_score": round((conf * 1000) / (base["cost"] * 10000), 2) # New Research Metric
    }
    
    incidents_db[request_id] = incident
    return incident

@app.post("/apply-fix")
def apply_fix(request_id: str, action: str):
    if request_id not in incidents_db:
        # Allow mock fix for demo fluidity
        logger.info(f"Applying fix to stateless request: {action}")
        return {"status": "HEALTHY", "mock": True}

    # Simulate Recovery
    inc = incidents_db[request_id]
    inc["status"] = "HEALTHY"
    resolved_incidents.append(inc)
    
    # Log Success
    logger.info(
        f"✅ Recovery Action Applied: {action}",
        extra={"props": {"request_id": request_id, "previous_risk": "mitigated"}}
    )
    
    emit_metric("sentinel.business.risk", 0, ["status:recovered"])
    
    return {
        "request_id": request_id,
        "status": "HEALTHY",
        "recovery_action": action,
        "confidence_recovered": 0.96,
        "execution_time_sec": random.randint(1, 5)
    }

@app.post("/calculate-cost-savings")
def calculate_cost_savings(req: CostRequest):
    # Pydantic validation handles the input
    try:
        cur_spec = MODEL_SPECS.get(req.current_model, MODEL_SPECS["gpt4"])
        rec_spec = MODEL_SPECS.get(req.recommended_model, MODEL_SPECS["gemini_1_5_flash"])
        
        cur_cost = req.monthly_requests * cur_spec["cost"]
        rec_cost = req.monthly_requests * rec_spec["cost"]
        savings = cur_cost - rec_cost
        
        return {
            "current_model_name": cur_spec["name"],
            "recommended_model_name": rec_spec["name"],
            "current_monthly_cost": round(cur_cost, 2),
            "recommended_monthly_cost": round(rec_cost, 2),
            "monthly_savings_usd": round(savings, 2),
            "annual_savings_usd": round(savings * 12, 2),
            "savings_percent": round((savings/cur_cost)*100, 1),
            "payback_period_days": 0.4,
            "model_specs": {"current": cur_spec, "recommended": rec_spec}
        }
    except Exception as e:
        logger.error(f"Calculator Error: {e}")
        raise HTTPException(status_code=500, detail="Calculation failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)