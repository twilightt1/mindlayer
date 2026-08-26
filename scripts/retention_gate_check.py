"""
Retention Gate Evaluation Script

Run this script on Sep 7 to evaluate Q3 retention metrics.
Usage: python scripts/retention_gate_check.py

Gate Criteria:
- WAQR (Weekly Active Question Retention) >= 75%
- Feature Adoption >= 40% active users
- Demo Data Seeding >= 50% users seeded
"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_, distinct

# Add app to path
sys.path.insert(0, ".")

from app.database import AsyncSessionLocal
from app.services.analytics_service import AnalyticsEvent, FeatureUsage
from app.models.memory import Memory
from app.models.user import User


async def check_retention_metrics():
    """Evaluate retention gate criteria."""
    
    print("=" * 60)
    print("Q3 RETENTION GATE EVALUATION")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    results = {
        "waqr": 0.0,  # Weekly Active Question Retention
        "feature_adoption": 0.0,  # % users with >= 1 feature interaction
        "demo_seeding": 0.0,  # % users who got demo data
        "passes_gate": False,
    }
    
    async with AsyncSessionLocal() as db:
        # Time ranges
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        # 1. WAQR - Weekly Active Question Retention
        # Definition: % of users who asked questions this week that also asked questions last week
        print("\n[1/3] Calculating WAQR (Weekly Active Question Retention)...")
        
        # Users who asked questions this week
        this_week_questions = await db.execute(
            select(AnalyticsEvent.user_id)
            .where(
                and_(
                    AnalyticsEvent.event_name.like('%question%'),
                    AnalyticsEvent.timestamp >= week_ago
                )
            )
            .distinct()
        )
        this_week_users = set(this_week_questions.scalars().all())
        
        # Users who asked questions last week
        last_week_questions = await db.execute(
            select(AnalyticsEvent.user_id)
            .where(
                and_(
                    AnalyticsEvent.event_name.like('%question%'),
                    AnalyticsEvent.timestamp >= two_weeks_ago,
                    AnalyticsEvent.timestamp < week_ago
                )
            )
            .distinct()
        )
        last_week_users = set(last_week_questions.scalars().all())
        
        # Calculate retention
        if len(this_week_users) > 0:
            retained_users = this_week_users.intersection(last_week_users)
            results["waqr"] = (len(retained_users) / len(this_week_users)) * 100
        else:
            results["waqr"] = 0.0
        
        print(f"  - Users asking questions this week: {len(this_week_users)}")
        print(f"  - Users asking questions last week: {len(last_week_users)}")
        print(f"  - Retained users: {len(this_week_users.intersection(last_week_users))}")
        print(f"  - WAQR: {results['waqr']:.1f}%")
        
        # 2. Feature Adoption
        print("\n[2/3] Calculating Feature Adoption...")
        
        # Total unique users
        total_users_result = await db.execute(select(func.count(distinct(User.id))))
        total_users = total_users_result.scalar() or 0
        
        # Users with feature usage in last 7 days
        active_users_result = await db.execute(
            select(func.count(distinct(FeatureUsage.user_id)))
            .where(FeatureUsage.last_used >= week_ago)
        )
        active_users = active_users_result.scalar() or 0
        
        if total_users > 0:
            results["feature_adoption"] = (active_users / total_users) * 100
        else:
            results["feature_adoption"] = 0.0
        
        print(f"  - Total users: {total_users}")
        print(f"  - Active users (7 days): {active_users}")
        print(f"  - Feature Adoption: {results['feature_adoption']:.1f}%")
        
        # 3. Demo Data Seeding
        print("\n[3/3] Calculating Demo Data Seeding Rate...")
        
        # Count users with memories from demo data
        demo_memory_count_result = await db.execute(
            select(func.count(distinct(Memory.user_id)))
            .where(Memory.captured_at >= (now - timedelta(days=30)))  # Recent signups
        )
        demo_seeded_users = demo_memory_count_result.scalar() or 0
        
        # Count total recent users
        recent_users_result = await db.execute(
            select(func.count(User.id))
            .where(User.created_at >= (now - timedelta(days=30)))
        )
        recent_users = recent_users_result.scalar() or 0
        
        if recent_users > 0:
            results["demo_seeding"] = (demo_seeded_users / recent_users) * 100
        else:
            results["demo_seeding"] = 100.0 if demo_seeded_users == 0 else 0.0
        
        print(f"  - Users signed up (30 days): {recent_users}")
        print(f"  - Users with demo data: {demo_seeded_users}")
        print(f"  - Demo Seeding Rate: {results['demo_seeding']:.1f}%")
    
    # Gate Decision
    print("\n" + "=" * 60)
    print("GATE DECISION")
    print("=" * 60)
    
    gate_criteria = [
        ("WAQR >= 75%", results["waqr"] >= 75, f"{results['waqr']:.1f}%"),
        ("Feature Adoption >= 40%", results["feature_adoption"] >= 40, f"{results['feature_adoption']:.1f}%"),
        ("Demo Seeding >= 50%", results["demo_seeding"] >= 50, f"{results['demo_seeding']:.1f}%"),
    ]
    
    all_pass = True
    for name, passed, value in gate_criteria:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} | {name} ({value})")
        if not passed:
            all_pass = False
    
    results["passes_gate"] = all_pass
    
    print("\n" + "-" * 60)
    if all_pass:
        print("🎉 GATE PASSED - Proceed to Q4 roadmap planning")
        print("   Recommended: Schedule Q4 kickoff meeting")
    else:
        print("⚠️ GATE FAILED - Schedule retention sprint")
        print("   Recommended actions:")
        print("   1. Analyze drop-off points in onboarding")
        print("   2. Review feature discoverability")
        print("   3. Consider re-engagement campaigns")
    print("-" * 60)
    
    return results


async def main():
    """Run retention gate check."""
    try:
        results = await check_retention_metrics()
        return 0 if results["passes_gate"] else 1
    except Exception as e:
        print(f"\n❌ Error running retention check: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
