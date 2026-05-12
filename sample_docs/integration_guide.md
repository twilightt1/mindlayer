# Integration Guide

This guide describes common third-party integrations for MindLayer workspaces,
including Slack, Zendesk, Stripe, and CRM systems.

## Slack Integration

Admins can connect Slack from **Admin → Integrations → Slack**. After connection,
support agents can ask MindLayer questions directly from selected channels.

Required Slack permissions:

- Read messages in selected channels.
- Post answers as the MindLayer bot.
- Open modals for citation previews.

## Zendesk Integration

The Zendesk integration allows agents to search support knowledge while replying
to tickets. MindLayer can attach cited answers as internal notes or public
replies.

## Stripe Integration

The Stripe integration syncs customer plan, payment status, and subscription
metadata. If Stripe sync fails, billing answers may show stale plan data.

Troubleshooting failed Stripe integration:

1. Confirm the Stripe restricted key has read access to customers, prices, and
   subscriptions.
2. Verify the webhook endpoint is enabled in Stripe.
3. Check that the signing secret matches the MindLayer configuration.
4. Replay the latest Stripe event from the Stripe dashboard.

## CRM Integration

Enterprise customers can sync account metadata from Salesforce or HubSpot. CRM
metadata is used only for support routing and is not embedded into the vector
index.
