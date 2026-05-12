# Demo Questions

Use these questions after uploading the sample documents to a conversation.

| Question | Expected source |
| --- | --- |
| How do I rotate an API key? | api_authentication_guide.md |
| Why am I getting a 401 error? | api_authentication_guide.md |
| Which plan supports SSO? | billing_and_plans_faq.md |
| What are the rate limits for the Pro plan? | billing_and_plans_faq.md |
| What are the webhook retry rules? | webhook_troubleshooting.md |
| How do I debug failed webhook delivery? | webhook_troubleshooting.md |
| How do I troubleshoot failed Stripe integration? | integration_guide.md |
| What Slack permissions are required? | integration_guide.md |
| Which version introduced hybrid retrieval? | product_release_notes.md |
| Which version added async ingestion? | product_release_notes.md |
| What is the response time for a SEV-1 incident? | incident_response_runbook.md |
| What should I check when Redis latency spikes? | incident_response_runbook.md |

## Suggested Demo Flow

1. Register and login.
2. Create a conversation named `MindLayer Demo`.
3. Upload every markdown file in this directory except `demo_questions.md`.
4. Wait until document status becomes `ready`.
5. Ask the questions above.
6. Confirm the answer includes source snippets and agent trace metadata.
