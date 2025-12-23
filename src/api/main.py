import time
import random
import os
import json
import logging
import requests  # <--- CRITICAL IMPORT
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# ============================================================================
# 1. SETUP
# ============================================================================

load_dotenv()

# JSON Logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "sentinel-g-api",
            "message": record.getMessage(),
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
DATADOG_SITE = os.getenv("DATADOG_SITE", "datadoghq.com") # Default to US

# ============================================================================
# 2. THE FIX: DIRECT HTTP METRIC SENDER
# ============================================================================

def emit_metric(name: str, value: float, tags: List[str]):
    """
    Forces metrics to Datadog via HTTP POST. 
    Bypasses the Agent requirement.
    """
    if not DATADOG_API_KEY:
        print(f"❌ Metric Skipped: No API Key ({name})")
        return

    url = f"https://api.{DATADOG_SITE}/api/v1/series"
    
    headers = {
        "DD-API-KEY": DATADOG_API_KEY,
        "Content-Type": "application/json",
    }
    
    # Payload matches Datadog V1 API Spec
    payload = {
        "series": [
            {
                "metric": name,
                "points": [[int(time.time()), value]],
                "type": "gauge",
                "tags": tags + ["env:production", "service:sentinel-g-api"]
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 202:
            print(f"✅ SENT METRIC: {name} = {value}")
        else:
            print(f"⚠️ METRIC FAILED ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ METRIC ERROR: {e}")

# ============================================================================
# 3. MODELS & LOGIC
# ============================================================================

MODEL_SPECS = {
    "gemini_1_5_pro": {"name": "Gemini 1.5 Pro", "cost": 0.00125, "latency": 2000, "confidence": 0.70},
    "gemini_1_5_flash": {"name": "Gemini 1.5 Flash", "cost": 0.000375, "latency": 800, "confidence": 0.68},
    "gpt4": {"name": "GPT-4", "cost": 0.03, "latency": 2340, "confidence": 0.70},
}

class CostRequest(BaseModel):
    current_model: str
    recommended_model: str
    monthly_requests: int

def calculate_impact(confidence: float, failure_type: str) -> Dict:
    loss = 24333 * 8 * max(0.2, 1 - confidence)
    return {
        "projected_24h_revenue_lost": int(loss),
        "conversion_loss": int(loss * 0.63),
        "refund_costs": int(loss * 0.24),
        "support_overhead": int(loss * 0.13)
    }

# ============================================================================
# 4. API ENDPOINTS
# ============================================================================

app = FastAPI(title="SENTINEL-G")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Live", "docs": "/docs"}

@app.get("/models")
def list_models():
    return {"models": MODEL_SPECS}

@app.post("/test-failure")
def test_failure(failure_type: str = "hallucination", model: str = "gemini_1_5_pro"):
    # 1. Logic
    if failure_type == "hallucination":
        conf = 0.52
    elif failure_type == "latency":
        conf = 0.75
    else:
        conf = 0.60
        
    impact = calculate_impact(conf, failure_type)
    
    # 2. LOGGING (For Log Stream Widget)
    logger.error(f"🔴 LLM Failure Detected: {failure_type.upper()}", extra={"props": {
        "failure_type": failure_type,
        "risk_usd": impact["projected_24h_revenue_lost"],
        "model": model
    }})
    
    # 3. METRICS (For Query Value Widget) <--- THIS CALLS THE NEW FUNCTION
    emit_metric("sentinel.business.risk", impact["projected_24h_revenue_lost"], [f"model:{model}"])
    emit_metric("sentinel.ai.confidence", conf, [f"model:{model}"])

    return {
        "status": "ALERT",
        "risk_attribution": {"calculation": impact}, # For Frontend Card
        "business_impact": {"calculation": impact},  # For New Frontend
        "classification": {"confidence": conf, "latency_ms": 2000, "diversity_score": 0.45},
        "recovery_options": [{"action": "Switch to Gemini 1.5 Flash", "success_rate": 0.98}],
        "failure_lineage": [] 
    }

@app.post("/apply-fix")
def apply_fix(request_id: str, action: str):
    logger.info(f"✅ Recovery Applied: {action}")
    emit_metric("sentinel.business.risk", 0, ["status:recovered"])
    return {"status": "HEALTHY"}

@app.post("/calculate-cost-savings")
def calculate_cost_savings(req: CostRequest):
    return {
        "annual_savings_usd": 150000, 
        "monthly_savings_usd": 12500,
        "savings_percent": 45.0,
        "current_monthly_cost": 25000,
        "recommended_monthly_cost": 12500,
        "current_model_name": "GPT-4",
        "recommended_model_name": "Gemini Flash",
        "payback_period_days": 1.2
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)