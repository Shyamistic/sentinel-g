# Datadog Detection Rules for SENTINEL-G

## Monitor Configuration

### Monitor 1: LLM Failure Detection

**Name:** SENTINEL-G LLM Failure Detection
**Type:** Event-based monitor
**Query:** `source:sentinel-g AND failure:*`

**Trigger:** Alert if at least 1 match in past 5 minutes
**Severity:** High
**Notification:**
🚨 LLM Failure Detected: {{event.tags.failure}}

Request ID: {{event.tags.request_id}}
Confidence: {{event.tags.confidence}}
Latency: {{event.tags.latency}}ms
Revenue at Risk: $194K+

Recovery Actions:

Fallback to Claude 3.5 (85% success)

Add semantic validation (70% success)

Increase confidence threshold (65% success)

Dashboard: http://localhost:5173

text

---

### Monitor 2: Recovery Success Rate

**Name:** SENTINEL-G Recovery Success
**Type:** Metric-based
**Query:** `avg:sentinel.recovery.executed{status:success}`

**Trigger:** If < 80% success rate over 1 hour
**Severity:** Medium
**Action:** Review failed recovery attempts

---

### Monitor 3: Datadog Event Volume

**Name:** SENTINEL-G Event Volume Spike
**Type:** Event-based
**Query:** `source:sentinel-g`

**Trigger:** If > 10 events per minute (possible DDoS/spam)
**Severity:** High
**Action:** Investigate root cause

---

## Alert Routing

Severity: High → Slack #incidents
Severity: Medium → Email to team
Severity: Low → Log only

text

---

## SLA Tracking

- **Detection Latency:** < 100ms
- **Datadog Event Delivery:** < 2 seconds
- **Recovery Execution:** < 30 seconds
- **Dashboard Update:** < 5 seconds