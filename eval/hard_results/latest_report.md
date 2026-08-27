# Orivory RAG Evaluation Report

Generated at: `2026-08-26T18:43:57.161909+00:00`

## Summary

| Metric | Value |
|---|---:|
| Total cases | 25 |
| Passed cases | 25 |
| Failed cases | 0 |
| Source hit rate | 100.0% |
| Keyword coverage | 100.0% |
| Citation rate | 80.0% |
| Fallback accuracy | 100.0% |
| Hallucination flag rate | 0.0% |
| Correction rate | 0.0% |
| Average latency | 0.8 ms |

## Per-case Results

| Status | ID | Category | Source hit | Keyword coverage | Citation | Fallback OK | Latency | Sources |
|---|---|---|---:|---:|---|---|---:|---|
| ✅ | hard_001 | multi_hop | 100.0% | 100.0% | yes | yes | 1.3 ms | product_release_notes.md, demo_questions.md, incident_response_runbook.md, api_authentication_guide.md, billing_and_plans_faq.md |
| ✅ | hard_002 | temporal_reasoning | 100.0% | 100.0% | yes | yes | 0.9 ms | billing_and_plans_faq.md, api_authentication_guide.md, demo_questions.md, integration_guide.md, product_release_notes.md |
| ✅ | hard_003 | procedural | 100.0% | 100.0% | yes | yes | 0.9 ms | incident_response_runbook.md, product_release_notes.md, integration_guide.md, demo_questions.md, webhook_troubleshooting.md |
| ✅ | hard_004 | cross_doc_reasoning | 100.0% | 100.0% | yes | yes | 1.3 ms | demo_questions.md, api_authentication_guide.md, webhook_troubleshooting.md, incident_response_runbook.md, integration_guide.md |
| ✅ | hard_005 | comparative | 100.0% | 100.0% | yes | yes | 1.0 ms | billing_and_plans_faq.md, demo_questions.md, api_authentication_guide.md, incident_response_runbook.md, product_release_notes.md |
| ✅ | hard_006 | multi_feature | 100.0% | 100.0% | yes | yes | 1.0 ms | billing_and_plans_faq.md, product_release_notes.md, demo_questions.md, api_authentication_guide.md, integration_guide.md |
| ✅ | hard_007 | numerical | 100.0% | 100.0% | yes | yes | 0.9 ms | webhook_troubleshooting.md, demo_questions.md, billing_and_plans_faq.md, integration_guide.md, incident_response_runbook.md |
| ✅ | hard_008 | scenario_based | 100.0% | 100.0% | yes | yes | 1.0 ms | incident_response_runbook.md, demo_questions.md, product_release_notes.md, billing_and_plans_faq.md, webhook_troubleshooting.md |
| ✅ | hard_009 | policy_lookup | 100.0% | 100.0% | yes | yes | 0.9 ms | billing_and_plans_faq.md, webhook_troubleshooting.md, demo_questions.md, integration_guide.md, api_authentication_guide.md |
| ✅ | hard_010 | exact_spec | 100.0% | 100.0% | yes | yes | 0.9 ms | api_authentication_guide.md, demo_questions.md, product_release_notes.md, webhook_troubleshooting.md, incident_response_runbook.md |
| ✅ | hard_011 | temporal_policy | 100.0% | 100.0% | yes | yes | 0.8 ms | api_authentication_guide.md, billing_and_plans_faq.md, demo_questions.md, integration_guide.md, webhook_troubleshooting.md |
| ✅ | hard_012 | troubleshooting | 100.0% | 100.0% | yes | yes | 0.9 ms | integration_guide.md, webhook_troubleshooting.md, demo_questions.md, billing_and_plans_faq.md, incident_response_runbook.md |
| ✅ | hard_013 | feature_tracking | 100.0% | 100.0% | yes | yes | 0.9 ms | product_release_notes.md, demo_questions.md, incident_response_runbook.md, api_authentication_guide.md, billing_and_plans_faq.md |
| ✅ | hard_014 | security | 100.0% | 100.0% | yes | yes | 1.2 ms | webhook_troubleshooting.md, integration_guide.md, api_authentication_guide.md, demo_questions.md, billing_and_plans_faq.md |
| ✅ | hard_015 | implicative_cross | 100.0% | 100.0% | yes | yes | 1.6 ms | billing_and_plans_faq.md, api_authentication_guide.md, demo_questions.md, integration_guide.md, product_release_notes.md |
| ✅ | hard_016 | permission_spec | 100.0% | 100.0% | yes | yes | 0.9 ms | integration_guide.md, demo_questions.md, incident_response_runbook.md, product_release_notes.md, webhook_troubleshooting.md |
| ✅ | hard_017 | comparative_cross | 100.0% | 100.0% | yes | yes | 0.9 ms | webhook_troubleshooting.md, demo_questions.md, product_release_notes.md, billing_and_plans_faq.md, incident_response_runbook.md |
| ✅ | hard_018 | procedural_complete | 100.0% | 100.0% | yes | yes | 0.9 ms | api_authentication_guide.md, demo_questions.md, incident_response_runbook.md, product_release_notes.md, integration_guide.md |
| ✅ | hard_019 | technical_deep | 100.0% | 100.0% | yes | yes | 0.9 ms | product_release_notes.md, incident_response_runbook.md, api_authentication_guide.md, webhook_troubleshooting.md, demo_questions.md |
| ✅ | hard_020 | escalation | 100.0% | 100.0% | yes | yes | 1.0 ms | incident_response_runbook.md, demo_questions.md, api_authentication_guide.md, integration_guide.md, product_release_notes.md |
| ✅ | fallback_001 | out_of_scope | 100.0% | 100.0% | no | yes | 0.0 ms | — |
| ✅ | fallback_002 | out_of_scope | 100.0% | 100.0% | no | yes | 0.0 ms | — |
| ✅ | fallback_003 | out_of_scope | 100.0% | 100.0% | no | yes | 0.0 ms | — |
| ✅ | fallback_004 | out_of_scope | 100.0% | 100.0% | no | yes | 0.0 ms | — |
| ✅ | fallback_005 | out_of_scope | 100.0% | 100.0% | no | yes | 0.0 ms | — |

## Failed / Warning Cases

All cases passed the deterministic evaluation thresholds.
## Recommendations

- Add failed or ambiguous production questions to the dataset.
- Investigate cases with low source hit before changing chunking or retriever weights.
- Track citation and fallback accuracy separately from in-scope retrieval quality.
- Use live/API evaluation as a separate non-blocking workflow when infrastructure and LLM keys are available.
