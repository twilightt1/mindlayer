# SupportMind RAG Evaluation Report

Generated at: `2026-06-10T06:45:03.988939+00:00`

## Summary

| Metric | Value |
|---|---:|
| Total cases | 18 |
| Passed cases | 18 |
| Failed cases | 0 |
| Source hit rate | 100.0% |
| Keyword coverage | 100.0% |
| Citation rate | 83.3% |
| Fallback accuracy | 100.0% |
| Hallucination flag rate | 0.0% |
| Correction rate | 0.0% |
| Average latency | 0.8 ms |

## Per-case Results

| Status | ID | Category | Source hit | Keyword coverage | Citation | Fallback OK | Latency | Sources |
|---|---|---|---:|---:|---|---|---:|---|
| ✅ | api_auth_001 | api_auth | 100.0% | 100.0% | yes | yes | 2.1 ms | api_authentication_guide.md, demo_questions.md, integration_guide.md, webhook_troubleshooting.md, product_release_notes.md |
| ✅ | api_auth_002 | api_auth | 100.0% | 100.0% | yes | yes | 0.8 ms | demo_questions.md, api_authentication_guide.md, webhook_troubleshooting.md |
| ✅ | api_auth_003 | api_auth | 100.0% | 100.0% | yes | yes | 0.9 ms | api_authentication_guide.md, integration_guide.md, webhook_troubleshooting.md, demo_questions.md, product_release_notes.md |
| ✅ | billing_001 | billing | 100.0% | 100.0% | yes | yes | 0.8 ms | billing_and_plans_faq.md, demo_questions.md, product_release_notes.md, integration_guide.md |
| ✅ | billing_002 | billing | 100.0% | 100.0% | yes | yes | 0.9 ms | billing_and_plans_faq.md, demo_questions.md, api_authentication_guide.md, incident_response_runbook.md, product_release_notes.md |
| ✅ | billing_003 | billing | 100.0% | 100.0% | yes | yes | 0.9 ms | billing_and_plans_faq.md, demo_questions.md, integration_guide.md, webhook_troubleshooting.md |
| ✅ | webhook_001 | webhooks | 100.0% | 100.0% | yes | yes | 1.0 ms | webhook_troubleshooting.md, demo_questions.md, billing_and_plans_faq.md, api_authentication_guide.md, incident_response_runbook.md |
| ✅ | webhook_002 | webhooks | 100.0% | 100.0% | yes | yes | 0.9 ms | webhook_troubleshooting.md, demo_questions.md, integration_guide.md, billing_and_plans_faq.md, product_release_notes.md |
| ✅ | webhook_003 | webhooks | 100.0% | 100.0% | yes | yes | 0.8 ms | webhook_troubleshooting.md, demo_questions.md, integration_guide.md, api_authentication_guide.md, billing_and_plans_faq.md |
| ✅ | integration_001 | integrations | 100.0% | 100.0% | yes | yes | 0.9 ms | integration_guide.md, demo_questions.md, webhook_troubleshooting.md, api_authentication_guide.md, billing_and_plans_faq.md |
| ✅ | integration_002 | integrations | 100.0% | 100.0% | yes | yes | 0.8 ms | integration_guide.md, demo_questions.md, api_authentication_guide.md, incident_response_runbook.md, webhook_troubleshooting.md |
| ✅ | release_001 | releases | 100.0% | 100.0% | yes | yes | 0.7 ms | product_release_notes.md, demo_questions.md, incident_response_runbook.md |
| ✅ | release_002 | releases | 100.0% | 100.0% | yes | yes | 0.8 ms | product_release_notes.md, demo_questions.md, incident_response_runbook.md, webhook_troubleshooting.md |
| ✅ | incident_001 | incidents | 100.0% | 100.0% | yes | yes | 0.8 ms | incident_response_runbook.md, demo_questions.md, api_authentication_guide.md, webhook_troubleshooting.md, product_release_notes.md |
| ✅ | incident_002 | incidents | 100.0% | 100.0% | yes | yes | 0.9 ms | demo_questions.md, incident_response_runbook.md, webhook_troubleshooting.md, api_authentication_guide.md, integration_guide.md |
| ✅ | fallback_001 | out_of_scope | 100.0% | 100.0% | no | yes | 0.0 ms | — |
| ✅ | fallback_002 | out_of_scope | 100.0% | 100.0% | no | yes | 0.0 ms | — |
| ✅ | fallback_003 | out_of_scope | 100.0% | 100.0% | no | yes | 0.0 ms | — |

## Failed / Warning Cases

All cases passed the deterministic evaluation thresholds.
## Recommendations

- Add failed or ambiguous production questions to the dataset.
- Investigate cases with low source hit before changing chunking or retriever weights.
- Track citation and fallback accuracy separately from in-scope retrieval quality.
- Use live/API evaluation as a separate non-blocking workflow when infrastructure and LLM keys are available.
