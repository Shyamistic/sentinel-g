# SENTINEL-G Architecture

## System Design

### Layer 1: Detection (Deterministic)

LLM Request
↓
Telemetry Capture
├→ Confidence score
├→ Latency
├→ Token count
├→ Diversity score
└→ Tool calls
↓
Failure Classifier
├→ Compare vs. thresholds
├→ Calculate severity score
└→ Assign failure class
↓
Classification Result
├→ Primary class (enum)
├→ Confidence (0-1)
└→ Business impact ($USD)

text

### Layer 2: Quantification (Business Impact)

Classification Result
↓
Risk Attribution Engine
├→ Base hourly revenue: $24,333 ($583K/day)
├→ Hours until detection: 8h (assumption)
├→ Failure severity: (1 - confidence) + latency_boost
└→ Projected 24h loss = base × hours × severity
↓
Impact Breakdown
├→ Conversion Loss: 63% of total
├→ Refund Costs: 24% of total
└→ Support Overhead: 13% of total

text

### Layer 3: Recovery (Automated)

Failure Detected
↓
Recovery Recommender
├→ Rank actions by success rate
├→ Estimate execution time
└→ Calculate recovery confidence
↓
3 Options Presented
1️⃣ Fast (2 min, 85% success) → Fallback model
2️⃣ Medium (30 min, 70% success) → Add validation
3️⃣ Slow (5 min, 65% success) → Increase threshold

text

### Layer 4: Observability (Datadog)

Failure Detected
↓
POST /api/v1/events
├→ Title: "🔴 LLM Failure: HALLUCINATION_RISK"
├→ Text: Full breakdown ($122K, metrics, actions)
├→ Tags: service:sentinel-g, failure:hallucination_risk
└→ Source: sentinel-g
↓
Datadog Event Explorer
├→ Event visible in real-time
├→ Searchable by source/tags
└→ Link to detail page
↓
Monitor Triggered
├→ Query: source:sentinel-g AND failure:*
├→ Incident auto-created
└→ Alert sent

text

## Data Flow

### Request Path

Frontend
↓ POST /test-failure?type=hallucination
Backend (FastAPI)
↓ classify_failure()
Classification (enum + scores)
↓ calculate_business_impact()
Risk Attribution ($USD)
↓ generate_recovery_options()
3 Ranked Actions
↓ send_datadog_event()
Datadog Event API
↓ 202 OK
Event Created in Datadog
↓
Frontend (polling /metrics)
↓
Dashboard Updates (RED)

text

### Recovery Path

User Clicks "Apply Fix"
↓ POST /apply-fix?request_id=req-xxx&action="..."
Backend processes recovery
↓ send_datadog_event() [recovery event]
Datadog Event (recovery action)
↓
Frontend polling detects recovery
↓
Dashboard Updates (GREEN)
↓
Resolved Incidents Log

text

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | FastAPI (Python) | API, failure detection |
| Frontend | React + Tailwind | Dashboard, UX |
| Observability | Datadog REST API | Events, monitoring |
| Deployment | Render + Vercel | Backend + frontend |
| Version Control | GitHub | Code repository |

## Failure Classification Logic

### Thresholds (Deterministic)

THRESHOLDS = {
"confidence_score": 0.70, # Must be >= 0.70
"latency_ms": 2340, # Must be <= 2340ms
"diversity_score": 0.50, # Must be >= 0.50
"response_length_tokens": 200, # Must be <= 200 tokens
}

text

### Failure Score Calculation

failure_score = 1.0 - confidence_score

if latency > threshold:
failure_score += 0.15 (latency penalty)

if tokens > threshold:
failure_score += 0.10 (verbosity penalty)

if diversity < threshold:
failure_score += 0.05 (diversity penalty)

failure_score = min(1.0, failure_score) (cap at 1.0)

text

### Classification Decision

if confidence < 0.70 and latency > 3200:
return HALLUCINATION_RISK

if latency > 4500:
return LATENCY_ANOMALY

if tokens > 500:
return COST_EXPLOSION

else:
return NO_FAILURE

text

## Business Impact Calculation

### Revenue Model (E-commerce)

Base Daily Revenue: $583,000
Base Hourly Revenue: $24,333

When failure occurs:
Hours until manual detection: 8 hours (assumption)
Failure severity: 0-1 (calculated from thresholds)

Projected Loss (24h) = Base_Hourly × Hours × Severity

Example:
Base: $24,333/hour
Hours: 8
Severity: 0.63 (from confidence 0.52)

Loss = $24,333 × 8 × 0.63 = $122,638

text

### Impact Breakdown

Total Loss = $122,638

Conversion Loss (63%):
Users not completing purchases
Loss: $77,262

Refund Costs (24%):
Customers requesting refunds
Loss: $29,433

Support Overhead (13%):
Support team handling complaints
Loss: $15,943

text

## Failure Lineage

### Timeline Visualization

t-12m: confidence_drift_begins
Confidence: 0.52 → Alert threshold approaching

t-6m: token_spike
Output tokens: 320 → Beyond normal range

t-2m: latency_acceleration
Latency: 3200ms → Significant slowdown

t+0m: failure_triggered
Classification: HALLUCINATION_RISK
Score: 0.78 (HIGH)

text

## Deployment Architecture

### Development

localhost:5173 (Frontend)
↓ fetch
localhost:8000 (Backend)
