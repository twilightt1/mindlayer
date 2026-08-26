# Q3 Retention Gate (Sep 7, 2025)

## Overview

The Q3 Retention Gate evaluates user engagement and retention metrics to determine if MindLayer is ready to proceed to Q4 or needs a retention-focused sprint.

## Gate Criteria

| Metric | Target | Description |
|--------|--------|-------------|
| **WAQR** | ≥ 75% | Weekly Active Question Retention - % of users asking questions this week who also asked last week |
| **Feature Adoption** | ≥ 40% | % of users with at least 1 feature interaction in 7 days |
| **Demo Seeding** | ≥ 50% | % of new users (30 days) who received demo data |

## Running the Gate Check

### Option 1: Automated Script (Recommended)

```bash
cd mindlayer
python scripts/retention_gate_check.py
```

### Option 2: Manual SQL Queries

```sql
-- WAQR
SELECT 
  COUNT(DISTINCT CASE WHEN timestamp >= NOW() - INTERVAL '7 days' THEN user_id END) as this_week,
  COUNT(DISTINCT CASE WHEN timestamp >= NOW() - INTERVAL '14 days' AND timestamp < NOW() - INTERVAL '7 days' THEN user_id END) as last_week
FROM analytics_events
WHERE event_name LIKE '%question%';

-- Feature Adoption
SELECT 
  COUNT(DISTINCT fu.user_id) as active_users,
  COUNT(DISTINCT u.id) as total_users,
  ROUND(COUNT(DISTINCT fu.user_id)::NUMERIC / NULLIF(COUNT(DISTINCT u.id), 0) * 100, 1) as adoption_pct
FROM feature_usage fu
CROSS JOIN users u
WHERE fu.last_used >= NOW() - INTERVAL '7 days';
```

## Gate Decision Matrix

| Result | Action |
|--------|--------|
| All 3 criteria pass | ✅ **PROCEED** to Q4 roadmap planning |
| 2/3 criteria pass | ⚠️ **CONDITIONAL** - Address lowest metric first |
| 1/3 criteria pass | ❌ **HOLD** - Retention sprint required |
| 0/3 criteria pass | 🚨 **CRITICAL** - Emergency retention investigation |

## If Gate Fails

### Root Cause Analysis
1. **Low WAQR**: Users not finding value in repeated queries
   - Review search quality
   - Check if demo data is engaging
   - Analyze question types being asked

2. **Low Feature Adoption**: Users not exploring features
   - Audit onboarding flow
   - Check for UX friction points
   - Verify analytics tracking

3. **Low Demo Seeding**: Technical issue with demo data
   - Check `/api/v1/demo/seed` endpoint
   - Verify demo_data_service is called on signup

### Retention Sprint Priorities
1. Onboarding optimization
2. In-app guidance improvements  
3. Re-engagement email campaign
4. Feature discovery prompts

## Q4 Preparation

If gate passes, prepare for Q4:
- [ ] Schedule Q4 kickoff meeting
- [ ] Draft Q4 roadmap proposal
- [ ] Budget allocation for growth initiatives

## Files

- `scripts/retention_gate_check.py` - Automated gate evaluation
- `SPRINT_PROGRESS_Q3.md` - Sprint tracking and metrics
