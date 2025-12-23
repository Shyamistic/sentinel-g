from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import Dict, List
import time
import os
import logging
import requests
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinel-g")

DATADOG_API_KEY = os.getenv("DATADOG_API_KEY")
DATADOG_SITE = os.getenv("DATADOG_SITE", "datadoghq.com")

# ------------------------------------------------------------------------------
# DATA MODELS
# ------------------------------------------------------------------------------
class LLMModel(str, Enum):
    GEMINI_1_5_PRO = "gemini_1_5_pro"
    GEMINI_1_5_FLASH = "gemini_1_5_flash"
    GPT4 = "gpt4"
    GPT4O = "gpt4o"
    CLAUDE3_OPUS = "claude3_opus"
    CLAUDE3_HAIKU = "claude3_haiku"

class FailureClass(str, Enum):
    HALLUCINATION_RISK = "HALLUCINATION_RISK"
    LATENCY_ANOMALY = "LATENCY_ANOMALY"
    COST_EXPLOSION = "COST_EXPLOSION"
    CONFIDENCE_DRIFT = "CONFIDENCE_DRIFT"

class CostRequest(BaseModel):
    current_model: LLMModel
    recommended_model: LLMModel
    monthly_requests: int

# ------------------------------------------------------------------------------
# CONFIGURATION & SPECS
# ------------------------------------------------------------------------------
MODEL_SPECS = {
    LLMModel.GEMINI_1_5_PRO: {"name": "Gemini 1.5 Pro", "cost": 0.00125, "latency": 2000, "confidence": 0.70, "max_tokens": 1000000, "confidence_threshold": 0.70},
    LLMModel.GEMINI_1_5_FLASH: {"name": "Gemini 1.5 Flash", "cost": 0.000375, "latency": 800, "confidence": 0.68, "max_tokens": 1000000, "confidence_threshold": 0.68},
    LLMModel.GPT4: {"name": "GPT-4", "cost": 0.03, "latency": 2340, "confidence": 0.70, "max_tokens": 8192, "confidence_threshold": 0.70},
    LLMModel.GPT4O: {"name": "GPT-4o", "cost": 0.015, "latency": 1200, "confidence": 0.72, "max_tokens": 128000, "confidence_threshold": 0.72},
    LLMModel.CLAUDE3_OPUS: {"name": "Claude 3 Opus", "cost": 0.015, "latency": 1800, "confidence": 0.75, "max_tokens": 200000, "confidence_threshold": 0.75},
    LLMModel.CLAUDE3_HAIKU: {"name": "Claude 3 Haiku", "cost": 0.00025, "latency": 900, "confidence": 0.68, "max_tokens": 200000, "confidence_threshold": 0.68},
}

INCIDENTS: Dict[str, dict] = {}

# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------
def send_datadog_metric(metric_name: str, value: float, tags: List[str]):
    if not DATADOG_API_KEY: return
    try:
        url = f"https://api.{DATADOG_SITE}/api/v1/series"
        headers = {"DD-API-KEY": DATADOG_API_KEY, "Content-Type": "application/json"}
        payload = {
            "series": [{
                "metric": metric_name,
                "points": [[int(time.time()), value]],
                "type": "gauge",
                "tags": tags + ["env:production", "service:sentinel-g"]
            }]
        }
        requests.post(url, json=payload, headers=headers, timeout=3)
    except Exception as e:
        logger.error(f"Datadog Metric Error: {str(e)}")

def send_datadog_event(title: str, text: str, tags: List[str], priority: str = "normal"):
    if not DATADOG_API_KEY: return
    try:
        url = f"https://api.{DATADOG_SITE}/api/v1/events"
        headers = {"DD-API-KEY": DATADOG_API_KEY, "Content-Type": "application/json"}
        payload = {
            "title": title, "text": text, "tags": tags,
            "source_type_name": "sentinel-g", "priority": priority,
            "alert_type": "error" if priority == "high" else "info"
        }
        requests.post(url, json=payload, headers=headers, timeout=3)
    except Exception as e:
        logger.error(f"Datadog Event Error: {str(e)}")

def calculate_business_impact(confidence: float) -> dict:
    loss = 24333 * 8 * max(0.15, 1 - confidence)
    return {
        "projected_24h_loss": round(loss),
        "conversion_loss": round(loss * 0.63),
        "refund_costs": round(loss * 0.24),
        "support_overhead": round(loss * 0.13),
    }

# ------------------------------------------------------------------------------
# API ENDPOINTS
# ------------------------------------------------------------------------------
app = FastAPI(title="SENTINEL-G", description="LLM Reliability Control Plane")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "operational", "service": "sentinel-g"}

# THIS WAS MISSING -> FIXES THE DROPDOWN ERROR
@app.get("/models")
def list_models():
    formatted_models = {}
    for model_enum, specs in MODEL_SPECS.items():
        formatted_models[model_enum.value] = specs
    return {"models": formatted_models}

@app.post("/test-failure")
def test_failure(failure_type: str = "hallucination", model: LLMModel = LLMModel.GEMINI_1_5_PRO):
    base = MODEL_SPECS[model]
    
    if failure_type == "hallucination":
        classification = {"class": FailureClass.HALLUCINATION_RISK, "confidence": 0.52, "latency": base["latency"] * 1.2}
    elif failure_type == "latency":
        classification = {"class": FailureClass.LATENCY_ANOMALY, "confidence": 0.75, "latency": 4500}
    else:
        classification = {"class": FailureClass.HALLUCINATION_RISK, "confidence": 0.52, "latency": base["latency"]}

    impact = calculate_business_impact(classification["confidence"])
    request_id = f"req-{int(time.time() * 1000)}"

    # Send Metrics
    send_datadog_metric("sentinel.ai.confidence_score", classification["confidence"], [f"model:{model.value}"])
    send_datadog_metric("sentinel.business.revenue_at_risk", impact["projected_24h_loss"], [f"model:{model.value}"])
    send_datadog_metric("sentinel.ai.latency", classification["latency"], [f"model:{model.value}"])

    send_datadog_event(
        title=f"🔴 {classification['class'].value} Detected",
        text=f"Model: {model.value}\nRisk: ${impact['projected_24h_loss']:,}",
        tags=[f"model:{model.value}", f"failure:{classification['class'].value}"],
        priority="high"
    )

    incident = {
        "request_id": request_id, "timestamp": datetime.utcnow().isoformat(),
        "model": model.value, "classification": classification,
        "business_impact": impact, "status": "ALERT",
        "recovery_options": [
            {"action": "Switch to Gemini 1.5 Flash", "success_rate": 0.98, "roi": "High"},
            {"action": "Enable Vertex AI Grounding", "success_rate": 0.92, "roi": "Medium"}
        ]
    }
    INCIDENTS[request_id] = incident
    return incident

@app.post("/calculate-cost-savings")
def calculate_cost_savings(request: CostRequest):
    try:
        current = MODEL_SPECS[request.current_model]
        target = MODEL_SPECS[request.recommended_model]

        current_monthly = request.monthly_requests * current["cost"] 
        target_monthly = request.monthly_requests * target["cost"] 
        savings = current_monthly - target_monthly

        return {
            "current_model": request.current_model.value,
            "recommended_model": request.recommended_model.value,
            "current_model_name": current["name"],
            "recommended_model_name": target["name"],
            "current_monthly_cost": round(current_monthly, 2),
            "recommended_monthly_cost": round(target_monthly, 2),
            "monthly_savings_usd": round(savings, 2),
            "annual_savings_usd": round(savings * 12, 2),
            "savings_percent": round((savings / current_monthly) * 100, 1) if current_monthly > 0 else 0,
            "payback_period_days": 0.5, # Mock calculation
            "model_specs": {
                "current": current,
                "recommended": target
            }
        }
    except Exception as e:
        logger.error(f"Calculator Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apply-fix")
def apply_fix(request_id: str, action: str):
    send_datadog_metric("sentinel.business.revenue_at_risk", 0, ["status:recovered"])
    send_datadog_event(title="🟢 System Recovered", text=f"Action: {action}", tags=["type:recovery"])
    return {"request_id": request_id, "status": "HEALTHY"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)