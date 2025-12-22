SENTINEL-G emits structured LLM failure and recovery events to Datadog
using the Datadog Events API.

Confirmed ingestion via HTTP 202 responses and returned event IDs.

Sample Events:

1) LLM Failure Detected – HALLUCINATION_RISK
   Event ID: 8424335797768006613
   Business Impact: $122,638
   Tags: service:sentinel-g, env:dev, failure:hallucination_risk

2) LLM Failure Detected – LATENCY_ANOMALY
   Event ID: 8424350924734846444
   Business Impact: $91,492
   Tags: service:sentinel-g, env:dev, failure:latency_anomaly

3) LLM Recovery Applied
   Event ID: 8424351176941961542
   Action: Enable response streaming
   Status: HEALTHY

Note:
Due to Datadog trial indexing limitations, events may not appear in the
Events Explorer UI. API ingestion is confirmed via successful responses
and event URLs returned by Datadog.
