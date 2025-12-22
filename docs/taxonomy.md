# SENTINEL-G Failure Taxonomy

Complete reference for all failure classes, thresholds, and recovery actions.

## Failure Classes

### 1. HALLUCINATION_RISK

**Definition:** Model generates confident but factually incorrect information.

**Triggers:**
- Confidence score < 0.70
- Response length > 200 tokens
- Latency anomaly detected

**Metrics:**
| Metric | Threshold | Status |
|--------|-----------|--------|
| Confidence | 0.70 | ❌ 0.52 |
| Latency | 2340ms | ❌ 3200ms |
| Diversity | 0.50 | ❌ 0.45 |

**Business Impact:**
- Conversion Loss: $77,262 (63%)
- Refund Costs: $29,433 (24%)
- Support Overhead: $15,943 (13%)
- **Total 24h Risk: $122,638**

**Recovery Actions:**

1. **Fallback to Claude 3.5 Sonnet (85% success, 2 min)**
   - Switch LLM provider to more reliable model
   - Maintain conversation context
   - Roll back after 30 minutes

2. **Add Semantic Validation Layer (70% success, 30 min)**
   - Verify output against known-good data
   - Implement fact-checking before response
   - Requires engineering effort

3. **Increase Confidence Threshold (65% success, 5 min)**
   - Only return responses with confidence > 0.80
   - Trade-off: Lower throughput, higher quality
   - Quick configuration change

---

### 2. LATENCY_ANOMALY

**Definition:** Response times exceed acceptable thresholds.

**Triggers:**
- Latency > 4500ms
- Consistency in slowness detected
- User experience impacted

**Metrics:**
| Metric | Threshold | Example |
|--------|-----------|---------|
| Latency | 2340ms | ❌ 4500ms |
| P99 Latency | 5000ms | ❌ 6200ms |
| Timeout Rate | <1% | ❌ 3.2% |

**Business Impact:**
- Cart Abandonment: Higher bounce rates
- User Frustration: Support tickets increase
- **Total 24h Risk: ~$91,492**

**Recovery Actions:**

1. **Enable Response Streaming (80% success, 5 min)**
   - Return tokens as they generate (no waiting)
   - Show progress to user
   - Perceived latency decreases

2. **Switch to Faster Model Variant (72% success, 2 min)**
   - Use Gemini Flash instead of Pro
   - Trade quality for speed
   - Monitor quality metrics

3. **Increase Timeout Threshold (55% success, 1 min)**
   - Allow longer response times
   - Risk: User experience still degraded
   - Short-term only

---

### 3. COST_EXPLOSION

**Definition:** Token usage explodes unexpectedly, inflating costs.

**Triggers:**
- Input tokens > 1200 (unusual prompts)
- Output tokens > 500 (verbose responses)
- Token ratio anomaly detected

**Metrics:**
| Metric | Threshold | Example |
|--------|-----------|---------|
| Input Tokens | 1200 | ❌ 1500 |
| Output Tokens | 500 | ❌ 820 |
| Cost/Request | $0.005 | ❌ $0.015 |

**Business Impact:**
- Unplanned infrastructure costs
- Margin compression on low-margin products
- **Total 24h Risk: ~$85,000**

**Recovery Actions:**

1. **Switch to Gemini 1.5 Flash (82% success, 3 min)**
   - 50% cost reduction
   - Slightly lower quality
   - Better for low-complexity requests

2. **Enable Prompt Caching (75% success, 15 min)**
   - Cache frequent prompts
   - Reuse for similar requests
   - 90% cost savings on cached tokens

3. **Reduce Context Window to 2K Tokens (60% success, 2 min)**
   - Limit input length
   - Trade: Less context = lower quality
   - Emergency-only option

---

### 4. DIVERSITY_COLLAPSE

**Definition:** Responses become repetitive/formulaic, lacking variety.

**Triggers:**
- Diversity score < 0.50
- Temperature too low
- Repetition patterns detected

**Metrics:**
| Metric | Threshold | Example |
|--------|-----------|---------|
| Diversity Score | 0.50 | ❌ 0.35 |
| Unique Tokens | 40% | ❌ 22% |
| Repetition Index | <20% | ❌ 45% |

**Business Impact:**
- Poor user experience
- Lower engagement
- Perceived low quality

**Recovery Actions:**

1. **Increase Temperature (0.7 → 1.0)**
   - Add randomness to generation
   - Increase output variety
   - Instant effect

2. **Add Diversity Penalty**
   - Penalize repeated tokens
   - Force model to explore alternatives
   - Requires prompt engineering

3. **Rotate Between Models**
   - Use different LLM for diversity
   - Blend outputs intelligently
   - Higher latency/cost

---

### 5. RETRY_DEPTH_EXCEEDED

**Definition:** System retries same request too many times (infinite loop risk).

**Triggers:**
- Retry count > 5
- Time spent retrying > 30 seconds
- Same error persists

**Metrics:**
| Metric | Threshold | Example |
|--------|-----------|---------|
| Retries | 5 | ❌ 8 |
| Retry Time | 30s | ❌ 45s |
| Success Rate After Retry | >70% | ❌ 15% |

**Business Impact:**
- Hung requests consuming resources
- User timeout/bad experience
- Infrastructure strain

**Recovery Actions:**

1. **Circuit Breaker Pattern**
   - Stop retrying after N failures
   - Return cached response
   - Fail fast, improve UX

2. **Exponential Backoff**
   - Wait longer between retries
   - Reduce load on failing service
   - Increase success probability

3. **Fallback to Default Response**
   - Use pre-generated response
   - Better than error to user
   - Log for debugging

---

### 6. TOKEN_LIMIT_BREACH

**Definition:** Request exceeds token limits (input or output).

**Triggers:**
- Total tokens > model limit
- Context window exceeded
- Generation hits max tokens

**Business Impact:**
- Request fails entirely
- User error message
- Poor experience

**Recovery Actions:**

1. **Truncate Context**
   - Keep only recent/relevant messages
   - Lose some context
   - Usually acceptable

2. **Split into Multiple Requests**
   - Break large request into chunks
   - Recombine results
   - Higher latency

3. **Switch to Model with Larger Context**
   - Gemini 1.5 Pro (1M tokens)
   - Higher cost
   - Solves problem immediately

---

### 7. CONFIDENCE_DRIFT

**Definition:** Model confidence gradually decreases (trend, not sudden).

**Triggers:**
- Confidence 0.70 → 0.60 → 0.50 (downward trend)
- 5+ consecutive below-threshold requests
- Drift detected over time window

**Metrics:**
| Metric | Threshold | Trend |
|--------|-----------|-------|
| Confidence | 0.70 | ↓ 0.65, 0.60, 0.52 |
| Drift Rate | <2%/min | ↓ 3%/min (ALERT) |

**Business Impact:**
- Early warning sign
- Not immediate failure yet
- Time to act before full failure

**Recovery Actions:**

1. **Proactive Model Switch**
   - Switch before complete failure
   - Prevent cascade
   - Best early-warning action

2. **Increase Training Data Quality**
   - Fine-tune on higher-quality examples
   - Address root cause
   - Long-term solution

3. **Monitor & Alert**
   - Set up Datadog monitor
   - Alert on drift >= 2%/min
   - Enable faster response

---

### 8. OUTPUT_VARIANCE

**Definition:** Same input produces wildly different outputs (inconsistency).

**Triggers:**
- Same prompt → different responses
- Response variance > threshold
- Unpredictable behavior detected

**Business Impact:**
- Trust issues
- Difficult to debug
- Reproducibility problems

**Recovery Actions:**

1. **Lower Temperature**
   - Reduce randomness
   - More consistent outputs
   - Might reduce quality

2. **Set Seed Value**
   - Deterministic generation
   - Reproducible results
   - Trade creative output

3. **Add Output Constraints**
   - Force structured format
   - Reduce variance by design
   - Engineering solution

---

### 9. TOOL_FAILURE

**Definition:** Tools/function calls invoked by LLM fail.

**Triggers:**
- Tool returns error
- Tool timeout
- Tool unavailable

**Business Impact:**
- Missing information
- Wrong answers
- Broken workflows

**Recovery Actions:**

1. **Retry Tool Call**
   - Transient failures often resolve
   - Exponential backoff
   - Success rate ~70%

2. **Fallback Tool**
   - Use alternative tool/API
   - May have different data
   - Better than nothing

3. **Skip Tool, Use Context**
   - Answer from existing context
   - Lower quality but functional
   - User still gets response

---

### 10. FREQUENCY_ANOMALY

**Definition:** Request rate abnormal (too high/low for typical pattern).

**Triggers:**
- Request rate > 10x normal
- Request rate < 10% normal
- Pattern deviation detected

**Business Impact:**
- Abuse/bot attack (high)
- Service degradation/issue (low)
- Infrastructure stress

**Recovery Actions:**

1. **Rate Limiting**
   - Cap requests per user/IP
   - Protect infrastructure
   - Prevent abuse

2. **Investigate Root Cause**
   - Check for bugs causing loops
   - Monitor for legitimate spikes
   - Adjust limits if needed

3. **Scale Infrastructure**
   - Add more capacity
   - Horizontal scaling
   - Long-term solution

---

## Threshold Reference Table

| Class | Confidence | Latency | Diversity | Tokens | Revenue Risk (24h) |
|-------|-----------|---------|-----------|--------|------------------|
| HALLUCINATION_RISK | <0.70 | >3200ms | <0.50 | >200 | $122,638 |
| LATENCY_ANOMALY | — | >4500ms | — | — | $91,492 |
| COST_EXPLOSION | — | — | — | >500 | $85,000 |
| DIVERSITY_COLLAPSE | — | — | <0.50 | — | $45,000 |
| RETRY_DEPTH_EXCEEDED | — | >30s retry | — | — | $20,000 |
| TOKEN_LIMIT_BREACH | — | — | — | >model_limit | $15,000 |
| CONFIDENCE_DRIFT | ↓ 2%/min | — | — | — | $50,000 |
| OUTPUT_VARIANCE | — | — | — | — | $30,000 |
| TOOL_FAILURE | — | >2s tool latency | — | — | $25,000 |
| FREQUENCY_ANOMALY | — | — | — | — | $40,000 |

---

## Recovery Confidence Scoring

Confidence = Success_Rate × (1 - Execution_Risk)

Success_Rate:
✓ Fallback Model: 85% (proven in production)
✓ Config Change: 70% (depends on parameters)
✓ Validation Layer: 65% (new code risk)

Execution_Risk:

Time required

Potential side effects

Rollback complexity

text

---

## Early Warning Signals

### Pre-Failure Indicators (t-12m to t+0m)

t-12m: Confidence drift begins (0.70 → 0.60)
Action: Monitor closely

t-6m: Token spike detected (200 → 300 tokens)
Action: Check prompts for complexity increase

t-2m: Latency acceleration (1200ms → 2500ms)
Action: Prepare recovery option

t+0m: Failure triggered (confidence < 0.70)
Action: Execute recovery

text

---

## Monitoring Checklist

- [ ] Confidence score trend (daily)
- [ ] Latency distribution (P50, P95, P99)
- [ ] Token usage growth (weekly)
- [ ] Diversity scoring (per batch)
- [ ] Retry rates (real-time)
- [ ] Tool failure rates (daily)
- [ ] Request frequency patterns (real-time)

---

## References

- Architecture: [`docs/architecture.md`](architecture.md)
- Deployment: `docs/deployment.md`
- API Docs: `http://localhost:8000/docs`