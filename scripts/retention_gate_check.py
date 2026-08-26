"""
Q3 Retention Gate Check - Mock/Simulation Version

This script simulates the retention gate check for demonstration.
In production, run with: python scripts/retention_gate_check.py

For production use:
1. Ensure DATABASE_URL, REDIS_URL, JWT_SECRET_KEY are set in .env
2. Run: python scripts/retention_gate_check.py
"""

import random
from datetime import datetime, timezone

# Simulated metrics (replace with real DB queries in production)
SIMULATED_METRICS = {
    # These would come from actual DB queries in production
    "waqr": 78.5,  # Weekly Active Question Retention %
    "feature_adoption": 42.3,  # % users with activity in 7 days
    "demo_seeding": 65.0,  # % new users with demo data
}

def check_retention_gate(metrics: dict) -> dict:
    """Evaluate retention gate criteria."""
    
    print("=" * 60)
    print("Q3 RETENTION GATE EVALUATION")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    # Extract metrics
    waqr = metrics.get("waqr", 0)
    feature_adoption = metrics.get("feature_adoption", 0)
    demo_seeding = metrics.get("demo_seeding", 0)
    
    # Define gate criteria
    gate_criteria = [
        ("WAQR >= 75%", waqr, waqr >= 75),
        ("Feature Adoption >= 40%", feature_adoption, feature_adoption >= 40),
        ("Demo Seeding >= 50%", demo_seeding, demo_seeding >= 50),
    ]
    
    # Calculate results
    results = {
        "waqr": waqr,
        "feature_adoption": feature_adoption,
        "demo_seeding": demo_seeding,
        "passes_gate": all(c[2] for c in gate_criteria),
        "criteria": []
    }
    
    # Display metrics
    print("\n📊 METRICS")
    print("-" * 40)
    print(f"  WAQR:              {waqr:.1f}%")
    print(f"  Feature Adoption:   {feature_adoption:.1f}%")
    print(f"  Demo Seeding:      {demo_seeding:.1f}%")
    
    # Evaluate criteria
    print("\n" + "=" * 60)
    print("GATE DECISION")
    print("=" * 60)
    
    all_pass = True
    for name, value, passed in gate_criteria:
        threshold = name.split(">= ")[1] if ">=" in name else "?"
        status = "✅ PASS" if passed else "❌ FAIL"
        results["criteria"].append({"name": name, "value": value, "passed": passed})
        
        print(f"  {status} | {name}")
        print(f"         Actual: {value:.1f}% | Target: {threshold}")
        
        if not passed:
            all_pass = False
    
    results["passes_gate"] = all_pass
    
    # Final decision
    print("\n" + "-" * 60)
    if all_pass:
        print("🎉 GATE PASSED")
        print("\nNext Steps:")
        print("  1. ✅ Proceed to Q4 roadmap planning")
        print("  2. 📅 Schedule Q4 kickoff meeting")
        print("  3. 📋 Review Q4 success metrics")
    else:
        print("⚠️ GATE FAILED")
        print("\nRecommended Actions:")
        print("  1. Analyze drop-off points in onboarding")
        print("  2. Review feature discoverability")
        print("  3. Consider re-engagement campaigns")
        print("  4. Schedule retention sprint")
    print("-" * 60)
    
    return results


def main():
    """Run retention gate check."""
    print("\n🔍 Simulating Q3 Retention Gate Check...\n")
    print("Note: In production, this script connects to the database")
    print("      For now, using simulated metrics.\n")
    
    results = check_retention_gate(SIMULATED_METRICS)
    
    print("\n📋 GATE RESULTS:")
    print(f"   Passes Gate: {'YES' if results['passes_gate'] else 'NO'}")
    
    return 0 if results["passes_gate"] else 1


if __name__ == "__main__":
    exit(main())
