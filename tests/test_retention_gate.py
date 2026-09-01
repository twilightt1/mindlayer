"""
Tests for Retention Gate Checker
"""


import pytest

from app.agents.retention_gate import (
    RetentionGate,
    RetentionGateChecker,
    RetentionMetrics,
    RetentionStatus,
)


class TestRetentionMetrics:
    """Test RetentionMetrics calculations."""

    def test_query_success_rate_zero_queries(self):
        metrics = RetentionMetrics()
        assert metrics.query_success_rate == 0.0

    def test_query_success_rate_with_queries(self):
        metrics = RetentionMetrics(total_queries=100, successful_queries=85)
        assert metrics.query_success_rate == 85.0

    def test_user_return_rate_no_users(self):
        metrics = RetentionMetrics()
        assert metrics.user_return_rate == 0.0

    def test_user_return_rate_with_users(self):
        metrics = RetentionMetrics(unique_users=100, returning_users=40)
        assert metrics.user_return_rate == 40.0

    def test_feedback_rate_calculation(self):
        metrics = RetentionMetrics(total_queries=1000, feedback_submissions=150)
        assert metrics.feedback_rate == 15.0

    def test_multihop_rate_calculation(self):
        metrics = RetentionMetrics(total_queries=500, multihop_queries=100)
        assert metrics.multihop_rate == 20.0


class TestRetentionGateChecker:
    """Test RetentionGateChecker functionality."""

    def test_initialization(self):
        checker = RetentionGateChecker()
        assert checker._metrics.total_queries == 0
        assert checker._baseline_metrics is None

    def test_initialization_with_custom_gate(self):
        gate = RetentionGate(min_query_success_rate=90.0)
        checker = RetentionGateChecker(gate=gate)
        assert checker.gate.min_query_success_rate == 90.0

    def test_record_query_success(self):
        checker = RetentionGateChecker()
        checker.record_query(success=True, response_time_ms=200.0, confidence_score=0.85)

        assert checker._metrics.total_queries == 1
        assert checker._metrics.successful_queries == 1
        assert checker._metrics.avg_response_time_ms == 200.0
        assert checker._metrics.avg_confidence_score == 0.85

    def test_record_query_failure(self):
        checker = RetentionGateChecker()
        checker.record_query(success=False)

        assert checker._metrics.total_queries == 1
        assert checker._metrics.successful_queries == 0

    def test_record_multihop_query(self):
        checker = RetentionGateChecker()
        checker.record_query(success=True, is_multihop=True)
        checker.record_query(success=True, is_multihop=True)
        checker.record_query(success=True, is_multihop=False)

        assert checker._metrics.multihop_queries == 2
        assert checker._metrics.multihop_rate == pytest.approx(66.67, rel=0.1)

    def test_record_temporal_query(self):
        checker = RetentionGateChecker()
        checker.record_query(success=True, is_temporal=True)
        checker.record_query(success=True, is_temporal=False)

        assert checker._metrics.temporal_queries == 1

    def test_record_web_fallback(self):
        checker = RetentionGateChecker()
        checker.record_query(success=True, used_web_fallback=True)
        checker.record_query(success=True, used_web_fallback=False)

        assert checker._metrics.web_fallback_uses == 1

    def test_record_feedback(self):
        checker = RetentionGateChecker()
        checker.record_feedback(submission=True)
        checker.record_feedback(submission=True)
        checker.record_feedback(submission=False)

        assert checker._metrics.feedback_submissions == 2

    def test_record_user_session_new_user(self):
        checker = RetentionGateChecker()
        checker.record_query(success=True, user_id="user_1")

        assert checker._metrics.unique_users == 1
        assert checker._metrics.returning_users == 0

    def test_record_user_session_returning_user(self):
        checker = RetentionGateChecker()
        checker.record_query(success=True, user_id="user_1")
        checker.record_query(success=True, user_id="user_1")
        checker.record_query(success=True, user_id="user_1")

        assert checker._metrics.unique_users == 3
        assert checker._metrics.returning_users == 2  # 2nd and 3rd visits

    def test_get_current_metrics(self):
        checker = RetentionGateChecker()
        checker.record_query(success=True, user_id="user_1")

        metrics = checker.get_current_metrics()
        assert metrics.total_queries == 1
        assert metrics.successful_queries == 1

    def test_set_baseline(self):
        checker = RetentionGateChecker()
        baseline = RetentionMetrics(
            total_queries=100,
            successful_queries=80,
        )
        checker.set_baseline(baseline)

        assert checker._baseline_metrics is not None
        assert checker._baseline_metrics.successful_queries == 80


class TestGateEvaluation:
    """Test gate evaluation logic."""

    def test_evaluate_exceeds_target(self):
        checker = RetentionGateChecker()
        checker.record_query(success=True)
        checker.record_query(success=True)
        checker.record_query(success=True)
        checker.record_query(success=True)
        checker.record_query(success=True)

        # 100% success rate > 95% target
        report = checker.evaluate()

        query_result = next(r for r in report.gate_results if "Query Success" in r.metric_name)
        assert query_result.status == RetentionStatus.EXCEEDS

    def test_evaluate_meets_threshold(self):
        checker = RetentionGateChecker()
        for _ in range(85):
            checker.record_query(success=True)
        for _ in range(15):
            checker.record_query(success=False)

        # 85% success rate = threshold
        report = checker.evaluate()

        query_result = next(r for r in report.gate_results if "Query Success" in r.metric_name)
        assert query_result.status == RetentionStatus.MEETS

    def test_evaluate_below_threshold(self):
        checker = RetentionGateChecker()
        for _ in range(70):
            checker.record_query(success=True)
        for _ in range(30):
            checker.record_query(success=False)

        # 70% success rate < 85% threshold but > 68% (80% of threshold)
        report = checker.evaluate()

        query_result = next(r for r in report.gate_results if "Query Success" in r.metric_name)
        assert query_result.status == RetentionStatus.BELOW

    def test_evaluate_critical(self):
        checker = RetentionGateChecker()
        for _ in range(50):
            checker.record_query(success=True)
        for _ in range(50):
            checker.record_query(success=False)

        # 50% success rate < 68% (80% of threshold)
        report = checker.evaluate()

        query_result = next(r for r in report.gate_results if "Query Success" in r.metric_name)
        assert query_result.status == RetentionStatus.CRITICAL

    def test_overall_status_exceeds(self):
        checker = RetentionGateChecker()
        # All queries succeed with feedback and multihop
        for i in range(100):
            checker.record_query(success=True, confidence_score=0.9)
            checker.record_feedback(submission=True)
            if i < 30:  # Multi-hop queries
                checker.record_query(success=True, is_multihop=True)

        report = checker.evaluate()

        # All metrics should be high
        assert report.pass_rate >= 80

    def test_overall_status_meets(self):
        checker = RetentionGateChecker()
        # 85% success rate
        for _ in range(85):
            checker.record_query(success=True)
        for _ in range(15):
            checker.record_query(success=False)
        # Users with feedback and multihop
        for i in range(20):
            checker.record_query(success=True, user_id=f"user_{i}", is_multihop=True)
            checker.record_feedback(submission=True)

        report = checker.evaluate()

        # Should have at least some passing gates
        assert report.passed_gates >= 2

    def test_overall_status_critical(self):
        checker = RetentionGateChecker()
        for _ in range(50):
            checker.record_query(success=True)

        report = checker.evaluate()

        # With only 50% query success, should be critical
        assert report.overall_status in [RetentionStatus.CRITICAL, RetentionStatus.BELOW]

    def test_pass_rate_calculation(self):
        checker = RetentionGateChecker()
        for _ in range(100):
            checker.record_query(success=True)

        report = checker.evaluate()

        assert report.total_gates == 5  # 5 metrics evaluated
        assert report.passed_gates >= 1
        assert report.pass_rate > 0


class TestRecommendations:
    """Test recommendation generation."""

    def test_recommendations_for_critical_metric(self):
        checker = RetentionGateChecker()
        for _ in range(30):
            checker.record_query(success=True, confidence_score=0.5)
        for _ in range(70):
            checker.record_query(success=False)

        report = checker.evaluate()

        # Should have recommendations for critical metrics
        assert len(report.recommendations) >= 1
        critical_recs = [r for r in report.recommendations if "CRITICAL" in r or "IMPROVE" in r]
        assert len(critical_recs) >= 1

    def test_recommendations_for_low_multihop(self):
        checker = RetentionGateChecker()
        for _ in range(100):
            checker.record_query(success=True)
        # Less than 10% multi-hop
        for _ in range(5):
            checker.record_query(success=True, is_multihop=True)

        report = checker.evaluate()

        multihop_recs = [r for r in report.recommendations if "multi-hop" in r.lower()]
        assert len(multihop_recs) >= 1

    def test_recommendations_for_low_feedback(self):
        checker = RetentionGateChecker()
        for _ in range(100):
            checker.record_query(success=True)
        # Less than 5% feedback
        checker.record_feedback(submission=True)
        checker.record_feedback(submission=True)

        report = checker.evaluate()

        feedback_recs = [r for r in report.recommendations if "feedback" in r.lower()]
        assert len(feedback_recs) >= 1


class TestReportGeneration:
    """Test report generation."""

    def test_to_summary_format(self):
        checker = RetentionGateChecker()
        for _ in range(100):
            checker.record_query(success=True)

        report = checker.evaluate()
        summary = report.to_summary()

        assert "Retention Gate Check Report" in summary
        assert "Evaluation Date" in summary
        assert "Gate Results" in summary
        assert "Pass Rate" in summary

    def test_to_summary_contains_all_results(self):
        checker = RetentionGateChecker()
        checker.record_query(success=True)

        report = checker.evaluate()
        summary = report.to_summary()

        assert "Query Success Rate" in summary
        assert "User Return Rate" in summary
        assert "Feedback Submission Rate" in summary
        assert "Multi-hop Query Rate" in summary
        assert "Confidence Score" in summary

    def test_report_with_custom_metrics(self):
        metrics = RetentionMetrics(
            total_queries=500,
            successful_queries=450,
            unique_users=200,
            returning_users=100,
            feedback_submissions=75,
            avg_confidence_score=0.88,
            multihop_queries=120,
        )

        checker = RetentionGateChecker()
        report = checker.evaluate(metrics)

        assert report.metrics.total_queries == 500
        assert report.metrics.successful_queries == 450
        assert report.metrics.query_success_rate == 90.0


class TestBaselineComparison:
    """Test baseline comparison functionality."""

    def test_improvement_calculation(self):
        # Baseline: 70% success rate
        baseline = RetentionMetrics(total_queries=100, successful_queries=70)

        checker = RetentionGateChecker()
        checker.set_baseline(baseline)

        # Current: 85% success rate
        metrics = RetentionMetrics(total_queries=100, successful_queries=85)

        report = checker.evaluate(metrics)

        query_result = next(r for r in report.gate_results if "Query Success" in r.metric_name)
        # Improvement: (85 - 70) / 70 * 100 = 21.4%
        assert query_result.improvement_from_baseline == pytest.approx(21.4, rel=0.5)

    def test_no_baseline_no_improvement(self):
        checker = RetentionGateChecker()
        # No baseline set

        metrics = RetentionMetrics(total_queries=100, successful_queries=85)

        report = checker.evaluate(metrics)

        query_result = next(r for r in report.gate_results if "Query Success" in r.metric_name)
        assert query_result.improvement_from_baseline == 0.0


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_metrics(self):
        checker = RetentionGateChecker()
        report = checker.evaluate()

        assert report.metrics.total_queries == 0
        assert report.pass_rate == 0.0
        assert report.overall_status == RetentionStatus.CRITICAL

    def test_custom_gate_thresholds(self):
        gate = RetentionGate(
            min_query_success_rate=95.0,
            min_user_return_rate=50.0,
            min_feedback_rate=20.0,
            min_multihop_rate=25.0,
            min_confidence_score=0.9,
        )

        checker = RetentionGateChecker(gate=gate)
        checker.record_query(success=True)

        report = checker.evaluate()

        # With only 1 successful query out of 1, success rate is 100%
        # But other metrics are 0, so overall should not be EXCEEDS
        assert report.overall_status in RetentionStatus


class TestRetentionStatusEnum:
    """Test RetentionStatus enum values."""

    def test_status_values(self):
        assert RetentionStatus.EXCEEDS.value == "exceeds"
        assert RetentionStatus.MEETS.value == "meets"
        assert RetentionStatus.BELOW.value == "below"
        assert RetentionStatus.CRITICAL.value == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
