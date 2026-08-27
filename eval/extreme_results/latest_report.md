# Orivory RAG Evaluation Report

Generated at: `2026-08-26T18:51:37.052797+00:00`

## Summary

| Metric | Value |
|---|---:|
| Total cases | 30 |
| Passed cases | 30 |
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
| ✅ | extreme_001 | multi_constraint_reasoning | 100.0% | 100.0% | yes | yes | 1.8 ms | incident_response_runbook.md, demo_questions.md, api_authentication_guide.md, webhook_troubleshooting.md, billing_and_plans_faq.md |
| ✅ | extreme_002 | edge_case_temporal | 100.0% | 100.0% | yes | yes | 0.9 ms | api_authentication_guide.md, incident_response_runbook.md, billing_and_plans_faq.md, demo_questions.md, integration_guide.md |
| ✅ | extreme_003 | multi_attribute_tradeoff | 100.0% | 100.0% | yes | yes | 0.9 ms | billing_and_plans_faq.md, integration_guide.md, demo_questions.md, product_release_notes.md, api_authentication_guide.md |
| ✅ | extreme_004 | contradiction_detection | 100.0% | 100.0% | yes | yes | 0.9 ms | api_authentication_guide.md, billing_and_plans_faq.md, demo_questions.md, integration_guide.md, product_release_notes.md |
| ✅ | extreme_005 | semantic_distinction | 100.0% | 100.0% | yes | yes | 0.9 ms | webhook_troubleshooting.md, billing_and_plans_faq.md, demo_questions.md, product_release_notes.md, api_authentication_guide.md |
| ✅ | extreme_006 | chain_reasoning | 100.0% | 100.0% | yes | yes | 0.9 ms | product_release_notes.md, incident_response_runbook.md, integration_guide.md, api_authentication_guide.md, demo_questions.md |
| ✅ | extreme_007 | role_permission_inference | 100.0% | 100.0% | yes | yes | 0.9 ms | api_authentication_guide.md, billing_and_plans_faq.md, integration_guide.md, product_release_notes.md, webhook_troubleshooting.md |
| ✅ | extreme_008 | numeric_temporal | 100.0% | 100.0% | yes | yes | 0.8 ms | incident_response_runbook.md, demo_questions.md, api_authentication_guide.md, integration_guide.md, webhook_troubleshooting.md |
| ✅ | extreme_009 | multi_system_diagnosis | 100.0% | 100.0% | yes | yes | 0.9 ms | incident_response_runbook.md, demo_questions.md, api_authentication_guide.md, webhook_troubleshooting.md, product_release_notes.md |
| ✅ | extreme_010 | policy_exception | 100.0% | 100.0% | yes | yes | 0.9 ms | billing_and_plans_faq.md, api_authentication_guide.md, integration_guide.md, demo_questions.md, incident_response_runbook.md |
| ✅ | extreme_011 | feature_version_mapping | 100.0% | 100.0% | yes | yes | 0.9 ms | product_release_notes.md, demo_questions.md, billing_and_plans_faq.md, incident_response_runbook.md, webhook_troubleshooting.md |
| ✅ | extreme_012 | causal_inference | 100.0% | 100.0% | yes | yes | 0.8 ms | integration_guide.md, demo_questions.md, webhook_troubleshooting.md, api_authentication_guide.md, billing_and_plans_faq.md |
| ✅ | extreme_013 | compound_calculation | 100.0% | 100.0% | yes | yes | 0.8 ms | webhook_troubleshooting.md, billing_and_plans_faq.md, demo_questions.md, incident_response_runbook.md, integration_guide.md |
| ✅ | extreme_014 | negative_action | 100.0% | 100.0% | yes | yes | 0.9 ms | incident_response_runbook.md, demo_questions.md, webhook_troubleshooting.md, product_release_notes.md, api_authentication_guide.md |
| ✅ | extreme_015 | abstract_relationship | 100.0% | 100.0% | yes | yes | 0.9 ms | product_release_notes.md, api_authentication_guide.md, billing_and_plans_faq.md, demo_questions.md, incident_response_runbook.md |
| ✅ | extreme_016 | boolean_inference | 100.0% | 100.0% | yes | yes | 1.2 ms | webhook_troubleshooting.md, integration_guide.md, demo_questions.md, billing_and_plans_faq.md, product_release_notes.md |
| ✅ | extreme_017 | temporal_sequencing | 100.0% | 100.0% | yes | yes | 0.9 ms | product_release_notes.md, demo_questions.md, incident_response_runbook.md |
| ✅ | extreme_018 | feature_independence | 100.0% | 100.0% | yes | yes | 1.0 ms | product_release_notes.md, billing_and_plans_faq.md, webhook_troubleshooting.md, demo_questions.md, api_authentication_guide.md |
| ✅ | extreme_019 | state_transition | 100.0% | 100.0% | yes | yes | 0.9 ms | billing_and_plans_faq.md, demo_questions.md, api_authentication_guide.md, incident_response_runbook.md, product_release_notes.md |
| ✅ | extreme_020 | false_premise | 100.0% | 100.0% | yes | yes | 0.9 ms | integration_guide.md, product_release_notes.md, demo_questions.md, incident_response_runbook.md, api_authentication_guide.md |
| ✅ | extreme_021 | order_dependency | 100.0% | 100.0% | yes | yes | 0.9 ms | api_authentication_guide.md, demo_questions.md, incident_response_runbook.md, integration_guide.md, product_release_notes.md |
| ✅ | extreme_022 | missing_data | 100.0% | 100.0% | yes | yes | 0.9 ms | incident_response_runbook.md, demo_questions.md, webhook_troubleshooting.md, api_authentication_guide.md, product_release_notes.md |
| ✅ | extreme_023 | implication_check | 100.0% | 100.0% | yes | yes | 0.8 ms | product_release_notes.md, billing_and_plans_faq.md, demo_questions.md, incident_response_runbook.md, integration_guide.md |
| ✅ | extreme_024 | limit_calculation | 100.0% | 100.0% | yes | yes | 1.0 ms | billing_and_plans_faq.md, api_authentication_guide.md, demo_questions.md, product_release_notes.md, incident_response_runbook.md |
| ✅ | extreme_025 | state_condition | 100.0% | 100.0% | yes | yes | 1.1 ms | product_release_notes.md, incident_response_runbook.md, integration_guide.md, demo_questions.md, webhook_troubleshooting.md |
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
