from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum
from datetime import datetime, timedelta
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
# DATADOG INTEGRATION
# ------------------------------------------------------------------------------

def send_datadog_event(
    title: str,
    text: str,
    tags: List[str],
    priority: str = "normal"
):
    if not DATADOG_API_KEY:
        return

    try:
        url = f"https://api.{DATADOG_SITE}/api/v1/events"
        headers = {
            "DD-API-KEY": DATADOG_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "title": title,
            "text": text,
            "tags": tags,
            "source_type_name": "sentinel-g",
            "priority": priority,
        }
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        logger.error(f"Datadog error: {str(e)}")

# ------------------------------------------------------------------------------
# MODELS & CONSTANTS
# ------------------------------------------------------------------------------

class LLMModel(str, Enum):
    GPT4 = "gpt4"
    GPT4O = "gpt4o"
    CLAUDE3 = "claude3"
    CLAUDE_HAIKU = "claude_haiku"
    GEMINI = "gemini"
    GEMINI_FLASH = "gemini_flash"

class FailureClass(str, Enum):
    HALLUCINATION_RISK = "HALLUCINATION_RISK"
    LATENCY_ANOMALY = "LATENCY_ANOMALY"
    COST_EXPLOSION = "COST_EXPLOSION"
    CONFIDENCE_DRIFT = "CONFIDENCE_DRIFT"
    DIVERSITY_COLLAPSE = "DIVERSITY_COLLAPSE"

MODEL_SPECS = {
    LLMModel.GPT4: {"cost": 0.03, "latency": 2340, "confidence": 0.70},
    LLMModel.GPT4O: {"cost": 0.015, "latency": 1200, "confidence": 0.72},
    LLMModel.CLAUDE3: {"cost": 0.015, "latency": 1800, "confidence": 0.75},
    LLMModel.CLAUDE_HAIKU: {"cost": 0.0008, "latency": 900, "confidence": 0.68},
    LLMModel.GEMINI: {"cost": 0.00175, "latency": 2000, "confidence": 0.70},
    LLMModel.GEMINI_FLASH: {"cost": 0.00075, "latency": 800, "confidence": 0.68},
}

# ------------------------------------------------------------------------------
# IN-MEMORY STATE (DEMO SAFE)
# ------------------------------------------------------------------------------

INCIDENTS: Dict[str, dict] = {}
RESOLVED: List[dict] = []

# ------------------------------------------------------------------------------
# CORE LOGIC
# ------------------------------------------------------------------------------

def classify_failure(failure_type: str, model: LLMModel) -> dict:
    base = MODEL_SPECS[model]

    if failure_type == "hallucination":
        return {
            "class": FailureClass.HALLUCINATION_RISK,
            "confidence": 0.52,
            "latency": base["latency"] * 1.4,
            "diversity": 0.45,
        }

    if failure_type == "latency":
        return {
            "class": FailureClass.LATENCY_ANOMALY,
            "confidence": 0.68,
            "latency": base["latency"] * 1.9,
            "diversity": 0.70,
        }

    if failure_type == "cost":
        return {
            "class": FailureClass.COST_EXPLOSION,
            "confidence": 0.65,
            "latency": base["latency"] * 1.2,
            "diversity": 0.66,
        }

    return classify_failure("hallucination", model)

def calculate_business_impact(confidence: float) -> dict:
    hourly_revenue = 24333
    hours_exposed = 8
    severity = max(0.15, 1 - confidence)

    loss = hourly_revenue * hours_exposed * severity

    return {
        "projected_24h_loss": round(loss),
        "conversion_loss": round(loss * 0.63),
        "refund_costs": round(loss * 0.24),
        "support_overhead": round(loss * 0.13),
    }

def recovery_playbook(failure: FailureClass, model: LLMModel) -> List[dict]:
    return [
        {
            "action": "Switch to Gemini 1.5 Flash",
            "target_model": "gemini_flash",
            "success_rate": 0.9,
            "execution_time_sec": 120,
            "roi": "High",
        },
        {
            "action": "Enable response streaming",
            "target_model": model.value,
            "success_rate": 0.8,
            "execution_time_sec": 300,
            "roi": "Medium",
        },
        {
            "action": "Increase confidence threshold",
            "target_model": model.value,
            "success_rate": 0.7,
            "execution_time_sec": 60,
            "roi": "Medium",
        },
    ]

# ------------------------------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------------------------------

app = FastAPI(
    title="SENTINEL-G",
    description="LLM Reliability Control Plane",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "sentinel-g",
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.post("/test-failure")
def test_failure(
    failure_type: str = "hallucination",
    model: LLMModel = LLMModel.GPT4,
):
    classification = classify_failure(failure_type, model)
    impact = calculate_business_impact(classification["confidence"])

    request_id = f"req-{int(time.time() * 1000)}"

    incident = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "model": model.value,
        "classification": {
            "primary_class": classification["class"].value,
            "confidence": classification["confidence"],
            "latency_ms": round(classification["latency"]),
            "diversity_score": classification["diversity"],
        },
        "business_impact": impact,
        "recovery_options": recovery_playbook(classification["class"], model),
        "status": "ALERT",
    }

    INCIDENTS[request_id] = incident

    send_datadog_event(
        title=f"🔴 LLM Failure Detected: {classification['class'].value}",
        text=f"""
Request ID: {request_id}
Model: {model.value}
Confidence: {classification['confidence']}
Latency: {round(classification['latency'])}ms
Projected 24h Impact: ${impact['projected_24h_loss']:,}
""",
        tags=[
            "service:sentinel-g",
            f"model:{model.value}",
            f"failure:{classification['class'].value.lower()}",
        ],
        priority="high",
    )

    return incident

@app.post("/apply-fix")
def apply_fix(request_id: str, action: str):
    if request_id not in INCIDENTS:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident = INCIDENTS[request_id]
    incident["status"] = "HEALTHY"

    RESOLVED.append(incident)

    send_datadog_event(
        title=f"✓ Recovery Applied: {action}",
        text=f"Request ID: {request_id}\nAction: {action}",
        tags=["service:sentinel-g", "type:recovery"],
    )

    return {
        "status": "HEALTHY",
        "execution_time_sec": 120,
        "confidence_recovered": 0.92,
        "latency_normalized_ms": 1500,
    }

@app.post("/calculate-cost-savings")
def calculate_cost_savings(
    current_model: LLMModel,
    recommended_model: LLMModel,
    monthly_requests: int,
):
    current = MODEL_SPECS[current_model]
    target = MODEL_SPECS[recommended_model]

    current_cost = monthly_requests * current["cost"]
    target_cost = monthly_requests * target["cost"]

    return {
        "current_monthly_cost": round(current_cost, 2),
        "optimized_monthly_cost": round(target_cost, 2),
        "monthly_savings": round(current_cost - target_cost, 2),
        "annual_savings": round((current_cost - target_cost) * 12, 2),
    }
