"""
Retention Gate Check for SOTA RAG Features
==========================================

Evaluates if implemented SOTA RAG features (CRAG, HyDE, Multi-hop, Temporal Memory, Feedback Pipeline)
are effectively retaining users and improving engagement.

Retention Gate Criteria:
- Query success rate >= 85%
- User feedback submission rate >= 10%
- Return usage within 7 days >= 40%
- Confidence score improvement >= 15%
- Multi-hop query handling >= 20% of queries
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class RetentionStatus(Enum):
    EXCEEDS = "exceeds"
    MEETS = "meets"
    BELOW = "below"
    CRITICAL = "critical"


@dataclass
class RetentionMetrics:
    """Current retention metrics snapshot."""

    # Query Metrics
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0

    # User Engagement Metrics
    unique_users: int = 0
    returning_users: int = 0
    feedback_submissions: int = 0

    # Quality Metrics
    avg_confidence_score: float = 0.0
    avg_response_time_ms: float = 0.0

    # Feature Usage
    multihop_queries: int = 0
    temporal_queries: int = 0
    web_fallback_uses: int = 0

    # Time Range
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)

    @property
    def query_success_rate(self) -> float:
        """Calculate query success rate."""
        if self.total_queries == 0:
            return 0.0
        return (self.successful_queries / self.total_queries) * 100

    @property
    def user_return_rate(self) -> float:
        """Calculate user return rate within 7 days."""
        if self.unique_users == 0:
            return 0.0
        return (self.returning_users / self.unique_users) * 100

    @property
    def feedback_rate(self) -> float:
        """Calculate feedback submission rate."""
        if self.total_queries == 0:
            return 0.0
        return (self.feedback_submissions / self.total_queries) * 100

    @property
    def multihop_rate(self) -> float:
        """Calculate multi-hop query percentage."""
        if self.total_queries == 0:
            return 0.0
        return (self.multihop_queries / self.total_queries) * 100


@dataclass
class RetentionGate:
    """Retention gate thresholds and evaluation."""

    # Minimum thresholds
    min_query_success_rate: float = 85.0
    min_user_return_rate: float = 40.0
    min_feedback_rate: float = 10.0
    min_multihop_rate: float = 20.0
    min_confidence_score: float = 0.7

    # Target thresholds (for "exceeds" status)
    target_query_success_rate: float = 95.0
    target_user_return_rate: float = 60.0
    target_feedback_rate: float = 15.0
    target_multihop_rate: float = 30.0
    target_confidence_score: float = 0.85


@dataclass
class GateResult:
    """Result of a single gate evaluation."""

    metric_name: str
    actual_value: float
    threshold: float
    target: float
    status: RetentionStatus
    improvement_from_baseline: float = 0.0


@dataclass
class RetentionGateReport:
    """Complete retention gate check report."""

    evaluation_date: datetime = field(default_factory=datetime.utcnow)
    metrics: RetentionMetrics = field(default_factory=RetentionMetrics)
    gate: RetentionGate = field(default_factory=RetentionGate)
    gate_results: list[GateResult] = field(default_factory=list)

    # Overall assessment
    overall_status: RetentionStatus = RetentionStatus.BELOW
    passed_gates: int = 0
    total_gates: int = 0
    pass_rate: float = 0.0

    # Recommendations
    recommendations: list[str] = field(default_factory=list)

    def to_summary(self) -> str:
        """Generate a human-readable summary."""
        status_emoji = {
            RetentionStatus.EXCEEDS: "🟢",
            RetentionStatus.MEETS: "🟡",
            RetentionStatus.BELOW: "🟠",
            RetentionStatus.CRITICAL: "🔴",
        }

        lines = [
            "# Retention Gate Check Report",
            "",
            f"**Evaluation Date:** {self.evaluation_date.strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Period:** {self.metrics.period_start.strftime('%Y-%m-%d')} to {self.metrics.period_end.strftime('%Y-%m-%d')}",
            "",
            f"## Overall Status: {status_emoji[self.overall_status]} {self.overall_status.value.upper()}",
            "",
            f"**Pass Rate:** {self.pass_rate:.1f}% ({self.passed_gates}/{self.total_gates} gates)",
            "",
            "## Gate Results",
            "",
        ]

        for result in self.gate_results:
            emoji = status_emoji[result.status]
            lines.append(f"| {emoji} {result.metric_name} | {result.actual_value:.1f}% | {result.threshold:.1f}% | {result.target:.1f}% |")

        if self.recommendations:
            lines.extend([
                "",
                "## Recommendations",
                "",
            ])
            for rec in self.recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)


class RetentionGateChecker:
    """
    Evaluates SOTA RAG features retention metrics.

    Usage:
        checker = RetentionGateChecker()
        checker.record_query(success=True, is_multihop=False)
        checker.record_feedback(submission=True)

        report = checker.evaluate()
        print(report.to_summary())
    """

    def __init__(self, gate: RetentionGate | None = None):
        self.gate = gate or RetentionGate()
        self._metrics = RetentionMetrics()
        self._baseline_metrics: RetentionMetrics | None = None
        self._user_sessions: dict[str, datetime] = {}

    def set_baseline(self, metrics: RetentionMetrics) -> None:
        """Set baseline metrics for comparison."""
        self._baseline_metrics = metrics

    def record_query(
        self,
        success: bool,
        response_time_ms: float = 0.0,
        confidence_score: float = 0.0,
        is_multihop: bool = False,
        is_temporal: bool = False,
        used_web_fallback: bool = False,
        user_id: str | None = None,
    ) -> None:
        """Record a query execution."""
        self._metrics.total_queries += 1

        if success:
            self._metrics.successful_queries += 1

        if response_time_ms > 0:
            # Running average
            n = self._metrics.total_queries
            self._metrics.avg_response_time_ms = (
                (self._metrics.avg_response_time_ms * (n - 1) + response_time_ms) / n
            )

        if confidence_score > 0:
            n = self._metrics.successful_queries
            self._metrics.avg_confidence_score = (
                (self._metrics.avg_confidence_score * (n - 1) + confidence_score) / n
            )

        if is_multihop:
            self._metrics.multihop_queries += 1

        if is_temporal:
            self._metrics.temporal_queries += 1

        if used_web_fallback:
            self._metrics.web_fallback_uses += 1

        # Track user sessions
        if user_id:
            self._metrics.unique_users += 1
            if user_id in self._user_sessions:
                self._metrics.returning_users += 1
            self._user_sessions[user_id] = datetime.utcnow()

    def record_feedback(self, submission: bool) -> None:
        """Record feedback submission."""
        if submission:
            self._metrics.feedback_submissions += 1

    def evaluate(self, metrics: RetentionMetrics | None = None) -> RetentionGateReport:
        """
        Evaluate retention gates and generate report.

        Args:
            metrics: Optional metrics to evaluate (uses recorded metrics if not provided)

        Returns:
            RetentionGateReport with evaluation results
        """
        eval_metrics = metrics or self._metrics

        report = RetentionGateReport(
            metrics=eval_metrics,
            gate=self.gate,
        )

        # Evaluate each metric
        results = []

        # Query Success Rate
        results.append(self._evaluate_metric(
            "Query Success Rate",
            eval_metrics.query_success_rate,
            self.gate.min_query_success_rate,
            self.gate.target_query_success_rate,
            "queries",
        ))

        # User Return Rate
        results.append(self._evaluate_metric(
            "User Return Rate (7-day)",
            eval_metrics.user_return_rate,
            self.gate.min_user_return_rate,
            self.gate.target_user_return_rate,
            "users",
        ))

        # Feedback Rate
        results.append(self._evaluate_metric(
            "Feedback Submission Rate",
            eval_metrics.feedback_rate,
            self.gate.min_feedback_rate,
            self.gate.target_feedback_rate,
            "feedback",
        ))

        # Multi-hop Rate
        results.append(self._evaluate_metric(
            "Multi-hop Query Rate",
            eval_metrics.multihop_rate,
            self.gate.min_multihop_rate,
            self.gate.target_multihop_rate,
            "multihop",
        ))

        # Confidence Score (percentage scale for comparison)
        confidence_pct = eval_metrics.avg_confidence_score * 100
        results.append(self._evaluate_metric(
            "Avg Confidence Score",
            confidence_pct,
            self.gate.min_confidence_score * 100,
            self.gate.target_confidence_score * 100,
            "confidence",
        ))

        report.gate_results = results
        report.passed_gates = sum(1 for r in results if r.status in (RetentionStatus.MEETS, RetentionStatus.EXCEEDS))
        report.total_gates = len(results)
        report.pass_rate = (report.passed_gates / report.total_gates) * 100 if report.total_gates > 0 else 0

        # Determine overall status
        critical_count = sum(1 for r in results if r.status == RetentionStatus.CRITICAL)
        below_count = sum(1 for r in results if r.status == RetentionStatus.BELOW)

        if critical_count > 0:
            report.overall_status = RetentionStatus.CRITICAL
        elif below_count == 0 and all(r.status == RetentionStatus.EXCEEDS for r in results):
            report.overall_status = RetentionStatus.EXCEEDS
        elif report.pass_rate >= 80:
            report.overall_status = RetentionStatus.MEETS
        elif report.pass_rate >= 50:
            report.overall_status = RetentionStatus.BELOW
        else:
            report.overall_status = RetentionStatus.CRITICAL

        # Generate recommendations
        report.recommendations = self._generate_recommendations(results)

        return report

    def _evaluate_metric(
        self,
        name: str,
        actual: float,
        threshold: float,
        target: float,
        metric_type: str,
    ) -> GateResult:
        """Evaluate a single metric against thresholds."""
        improvement = 0.0
        if self._baseline_metrics:
            baseline_value = self._get_baseline_value(metric_type)
            if baseline_value > 0:
                improvement = ((actual - baseline_value) / baseline_value) * 100

        # Determine status
        if actual >= target:
            status = RetentionStatus.EXCEEDS
        elif actual >= threshold:
            status = RetentionStatus.MEETS
        elif actual >= threshold * 0.8:  # Within 20% of threshold
            status = RetentionStatus.BELOW
        else:
            status = RetentionStatus.CRITICAL

        return GateResult(
            metric_name=name,
            actual_value=actual,
            threshold=threshold,
            target=target,
            status=status,
            improvement_from_baseline=improvement,
        )

    def _get_baseline_value(self, metric_type: str) -> float:
        """Get baseline value for a metric type."""
        if not self._baseline_metrics:
            return 0.0

        baselines = {
            "queries": self._baseline_metrics.query_success_rate,
            "users": self._baseline_metrics.user_return_rate,
            "feedback": self._baseline_metrics.feedback_rate,
            "multihop": self._baseline_metrics.multihop_rate,
            "confidence": self._baseline_metrics.avg_confidence_score * 100,
        }
        return baselines.get(metric_type, 0.0)

    def _generate_recommendations(self, results: list[GateResult]) -> list[str]:
        """Generate recommendations based on gate results."""
        recommendations = []

        for result in results:
            if result.status == RetentionStatus.CRITICAL:
                recommendations.append(
                    f"CRITICAL: {result.metric_name} is {result.actual_value:.1f}% "
                    f"(threshold: {result.threshold:.1f}%) - immediate action required"
                )
            elif result.status == RetentionStatus.BELOW:
                recommendations.append(
                    f"IMPROVE: {result.metric_name} at {result.actual_value:.1f}% "
                    f"(target: {result.target:.1f}%) - optimization needed"
                )

        # Feature-specific recommendations
        multihop_result = next((r for r in results if "Multi-hop" in r.metric_name), None)
        if multihop_result and multihop_result.actual_value < 10:
            recommendations.append(
                "Consider promoting multi-hop query detection to handle more complex queries"
            )

        feedback_result = next((r for r in results if "Feedback" in r.metric_name), None)
        if feedback_result and feedback_result.actual_value < 5:
            recommendations.append(
                "User feedback rate is low - consider making feedback collection less intrusive"
            )

        confidence_result = next((r for r in results if "Confidence" in r.metric_name), None)
        if confidence_result and confidence_result.actual_value < 60:
            recommendations.append(
                "Low confidence scores detected - review retrieval quality and CRAG thresholds"
            )

        if not recommendations:
            recommendations.append("All retention gates passing - continue monitoring")

        return recommendations

    def get_current_metrics(self) -> RetentionMetrics:
        """Get current recorded metrics."""
        return self._metrics


def create_sample_report() -> RetentionGateReport:
    """Create a sample retention gate report for demonstration."""
    # Sample metrics
    metrics = RetentionMetrics(
        total_queries=1000,
        successful_queries=920,
        failed_queries=80,
        unique_users=450,
        returning_users=220,
        feedback_submissions=150,
        avg_confidence_score=0.82,
        avg_response_time_ms=250.0,
        multihop_queries=280,
        temporal_queries=180,
        web_fallback_uses=120,
        period_start=datetime.utcnow() - timedelta(days=7),
        period_end=datetime.utcnow(),
    )

    checker = RetentionGateChecker()
    return checker.evaluate(metrics)


if __name__ == "__main__":
    # Demo
    report = create_sample_report()
    print(report.to_summary())
