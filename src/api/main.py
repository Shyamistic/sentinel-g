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
# 1. ENTERPRISE LOGGING & DATADOG SETUP
# ============================================================================

load_dotenv()

# JSON Formatter (This creates the "Screenshot 1840" Datadog Logs)
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
# 2. DATA MODELS & CONSTANTS
# ============================================================================

class LLMModel(str, Enum):
    GEMINI_1_5_PRO = "gemini_1_5_pro"
    GEMINI_1_5_FLASH = "gemini_1_5_flash"
    GPT4 = "gpt4"
    GPT4O = "gpt4o"

class FailureClass(str, Enum):
    HALLUCINATION_RISK = "HALLUCINATION_RISK"
    LATENCY_ANOMALY = "LATENCY_ANOMALY"
    COST_EXPLOSION = "COST_EXPLOSION"
    PROMPT_INJECTION = "PROMPT_INJECTION_ATTEMPT"
    TONAL_DRIFT = "TONAL_DRIFT_HOSTILE"

class CostRequest(BaseModel):
    current_model: str
    recommended_model: str
    monthly_requests: int

MODEL_SPECS = {
    "gemini_1_5_pro": {"name": "Gemini 1.5 Pro", "cost": 0.00125, "latency": 2000, "confidence": 0.70},
    "gemini_1_5_flash": {"name": "Gemini 1.5 Flash", "cost": 0.000375, "latency": 800, "confidence": 0.68},
    "gpt4": {"name": "GPT-4", "cost": 0.03, "latency": 2340, "confidence": 0.70},
    "gpt4o": {"name": "GPT-4o", "cost": 0.015, "latency": 1200, "confidence": 0.72},
}

incidents_db = {}
resolved_incidents = []

# ============================================================================
# 3. HELPER FUNCTIONS
# ============================================================================

def emit_metric(name: str, value: float, tags: List[str]):
    if DATADOG_AVAILABLE:
        try:
            api.Metric.send(metric=name, points=value, tags=tags, type="gauge")
        except Exception:
            pass

def calculate_impact(confidence: float, failure_type: str) -> Dict:
    base_revenue = 24333 # Hourly
    severity = max(0.2, 1 - confidence)
    
    if failure_type == "injection":
        severity = 1.0 
        
    loss = base_revenue * 8 * severity 
    
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
    if failure_class == FailureClass.HALLUCINATION_RISK:
        return [
            {"rank": 1, "action": "Enable Vertex AI Grounding", "success_rate": 0.94, "execution_time_min": 1, "roi": "High"},
            {"rank": 2, "action": "Switch to Gemini 1.5 Pro (High Reasoning)", "success_rate": 0.88, "execution_time_min": 2, "roi": "Medium"},
            {"rank": 3, "action": "Inject Self-Correction Prompt", "success_rate": 0.65, "execution_time_min": 5, "roi": "Low"}
        ]
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

# --- FIX 1: ROOT ENDPOINT (Stops the 404 errors) ---
@app.get("/")
def root():
    return {"service": "Sentinel-G API", "status": "Live", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "operational", "datadog": DATADOG_AVAILABLE, "timestamp": datetime.utcnow().isoformat()}

@app.get("/models")
def list_models():
    return {"models": MODEL_SPECS}

@app.post("/test-failure")
def test_failure(failure_type: str = "hallucination", model: str = "gemini_1_5_pro"):
    request_id = f"req-{int(time.time() * 1000)}"
    base = MODEL_SPECS.get(model, MODEL_SPECS["gemini_1_5_pro"])
    
    # 1. Logic
    if failure_type == "hallucination":
        cls = FailureClass.HALLUCINATION_RISK
        conf = 0.52
    elif failure_type == "latency":
        cls = FailureClass.LATENCY_ANOMALY
        conf = 0.75
    else:
        cls = FailureClass.COST_EXPLOSION
        conf = 0.60

    # 2. Data Construction
    impact = calculate_impact(conf, failure_type)
    recovery = get_recovery_options(cls)
    
    # 3. Logging (Structured for Datadog)
    logger.error(
        f"🔴 LLM Failure Detected: {cls.value}",
        extra={"props": {
            "request_id": request_id,
            "model": model,
            "failure_type": failure_type,
            "risk_usd": impact["calculation"]["projected_24h_revenue_lost"]
        }}
    )
    
    # Metrics
    emit_metric("sentinel.ai.confidence", conf, [f"model:{model}"])
    emit_metric("sentinel.business.risk", impact["calculation"]["projected_24h_revenue_lost"], [f"model:{model}"])

    # --- FIX 2: RESTORE 'risk_attribution' KEY ---
    incident = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "model": model,
        "classification": {
            "primary_class": cls.value,
            "confidence": conf,
            "latency_ms": base["latency"],
            "diversity_score": 0.45,
            "tokens_output": 320
        },
        # Critical: Sending BOTH keys ensures frontend compatibility
        "business_impact": impact,       # For new components
        "risk_attribution": impact,      # For your existing BusinessImpact.jsx
        "recovery_options": recovery,
        "failure_lineage": [
             {"time_marker": "t-5m", "signal": "early_warning", "value": 0.6, "description": "Drift detected", "timestamp": datetime.utcnow().isoformat()},
             {"time_marker": "t+0m", "signal": "failure", "value": 1.0, "description": "Threshold breached", "timestamp": datetime.utcnow().isoformat()}
        ],
        "status": "ALERT"
    }
    
    incidents_db[request_id] = incident
    return incident

@app.post("/apply-fix")
def apply_fix(request_id: str, action: str):
    logger.info(f"✅ Recovery Applied: {action}", extra={"props": {"request_id": request_id}})
    emit_metric("sentinel.business.risk", 0, ["status:recovered"])
    return {"request_id": request_id, "status": "HEALTHY"}

@app.post("/calculate-cost-savings")
def calculate_cost_savings(req: CostRequest):
    try:
        cur = MODEL_SPECS.get(req.current_model, MODEL_SPECS["gpt4"])
        rec = MODEL_SPECS.get(req.recommended_model, MODEL_SPECS["gemini_1_5_flash"])
        savings = (req.monthly_requests * cur["cost"]) - (req.monthly_requests * rec["cost"])
        
        return {
            "current_model_name": cur["name"],
            "recommended_model_name": rec["name"],
            "current_monthly_cost": round(req.monthly_requests * cur["cost"], 2),
            "recommended_monthly_cost": round(req.monthly_requests * rec["cost"], 2),
            "monthly_savings_usd": round(savings, 2),
            "annual_savings_usd": round(savings * 12, 2),
            "savings_percent": round((savings/(req.monthly_requests * cur["cost"]))*100, 1),
            "payback_period_days": 0.5,
            "model_specs": {"current": cur, "recommended": rec}
        }
    except Exception as e:
        logger.error(f"Calc Error: {e}")
        raise HTTPException(status_code=500, detail="Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)