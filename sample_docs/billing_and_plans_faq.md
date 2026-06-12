# Billing and Plans FAQ

This FAQ explains MindLayer subscription plans, limits, billing behavior, and
upgrade rules for a personal self-hosted workspace.

## Plans

MindLayer has three plans:

| Plan | Monthly conversations | Documents | SSO | Webhooks |
| --- | ---: | ---: | --- | --- |
| Starter | 1,000 | 100 | No | Basic |
| Pro | 10,000 | 2,000 | No | Advanced |
| Enterprise | Custom | Custom | Yes | Advanced |

## SSO Availability

Single Sign-On is available only on the **Enterprise** plan. Enterprise customers
can configure SAML or OIDC through **Admin → Security → Single Sign-On**.

## Rate Limits

Starter workspaces allow 60 requests per minute. Pro workspaces allow 300
requests per minute. Enterprise workspaces receive custom rate limits defined in
their contract.

## Upgrades

Plan upgrades take effect immediately. The billing system prorates the remaining
billing cycle and charges the difference on the next invoice.

## Downgrades

Plan downgrades take effect at the end of the current billing cycle. If the
workspace exceeds the target plan limits, admins must archive documents or reduce
usage before the downgrade can be completed.

## Failed Payments

If a payment fails, the workspace enters a 7-day grace period. During the grace
period, users can continue querying documents, but admins cannot upload new
documents until payment is resolved.
