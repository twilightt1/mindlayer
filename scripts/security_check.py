from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from app.services.diagnostics_service import build_config_summary  # noqa: E402


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


class SecurityCheckFailure(RuntimeError):
    pass


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _base_production_settings(**overrides) -> dict[str, object]:
    values: dict[str, object] = {
        "DATABASE_URL": "postgresql+asyncpg://mindlayer:strong-db-password@postgres:5432/ragdb",
        "REDIS_URL": "redis://redis:6379/0",
        "JWT_SECRET_KEY": "production-secret-key-with-more-than-32-characters",
        "MINIO_ACCESS_KEY": "mindlayer-prod-minio",
        "MINIO_SECRET_KEY": "mindlayer-prod-minio-secret",
        "OPENROUTER_API_KEY": "sk-or-production",
        "OPENAI_API_KEY": "sk-production",
        "JINA_API_KEY": "jina-production",
        "ALLOWED_ORIGINS": "https://app.mindlayer.example",
        "FRONTEND_URL": "https://app.mindlayer.example",
        "ENVIRONMENT": "production",
    }
    values.update(overrides)
    return values


def _expect_validation_error(name: str, match: str, **overrides) -> CheckResult:
    try:
        Settings(**_base_production_settings(**overrides))
    except ValidationError as exc:
        if re.search(match, str(exc), re.IGNORECASE):
            return CheckResult(name, "PASS", f"Rejected unsafe production settings: {match}")
        return CheckResult(name, "FAIL", f"Rejected settings, but not for expected reason: {exc}")
    return CheckResult(name, "FAIL", "Unsafe production settings were accepted")


def check_production_accepts_safe_settings() -> CheckResult:
    settings = Settings(**_base_production_settings())
    if not settings.is_production:
        return CheckResult("production safe settings", "FAIL", "Production settings did not normalize to production")
    return CheckResult("production safe settings", "PASS", "Complete safe production settings are accepted")


def check_jwt_placeholder_rejected() -> CheckResult:
    return _expect_validation_error(
        "placeholder JWT secret",
        "JWT_SECRET_KEY",
        JWT_SECRET_KEY="change-me-to-a-random-256-bit-secret",
    )


def check_wildcard_cors_rejected() -> CheckResult:
    return _expect_validation_error("wildcard CORS", "ALLOWED_ORIGINS", ALLOWED_ORIGINS="*")


def check_default_minio_rejected() -> CheckResult:
    return _expect_validation_error("default MinIO credentials", "Default MinIO", MINIO_ACCESS_KEY="minioadmin")


def check_provider_keys_required() -> CheckResult:
    return _expect_validation_error("required provider keys", "OPENAI_API_KEY", OPENAI_API_KEY="")


def _service_block(compose_text: str, service_name: str) -> str:
    pattern = rf"(?ms)^  {re.escape(service_name)}:\n(?P<body>.*?)(?=^  [a-zA-Z0-9_-]+:|^volumes:|\Z)"
    match = re.search(pattern, compose_text)
    if not match:
        raise SecurityCheckFailure(f"Service {service_name!r} not found in production compose")
    return match.group("body")


def check_internal_ports_removed() -> CheckResult:
    compose_text = _read("docker-compose.prod.yml")
    services = ["postgres", "redis", "chromadb", "minio", "flower"]
    missing: list[str] = []
    for service in services:
        block = _service_block(compose_text, service)
        if "ports: []" not in block:
            missing.append(service)
    if missing:
        return CheckResult("production internal ports", "FAIL", f"Missing ports: [] for {', '.join(missing)}")
    return CheckResult("production internal ports", "PASS", "Internal service host ports are removed in prod override")


def check_flower_ops_profile() -> CheckResult:
    block = _service_block(_read("docker-compose.prod.yml"), "flower")
    if "profiles:" in block and "- ops" in block:
        return CheckResult("flower ops profile", "PASS", "Flower is behind the ops profile in prod override")
    return CheckResult("flower ops profile", "FAIL", "Flower is not isolated behind the ops profile")


def check_admin_diagnostics_auth() -> CheckResult:
    admin_py = _read("app/api/v1/admin.py")
    pattern = r'@router\.get\("/diagnostics".*?async def get_diagnostics\(.*?Depends\(require_admin\)'
    if re.search(pattern, admin_py, flags=re.DOTALL):
        return CheckResult("admin diagnostics auth", "PASS", "Diagnostics endpoint depends on require_admin")
    return CheckResult("admin diagnostics auth", "FAIL", "Diagnostics endpoint does not clearly require admin auth")


def check_diagnostics_summary_safe() -> CheckResult:
    summary = build_config_summary()
    forbidden_keys = {
        "DATABASE_URL",
        "REDIS_URL",
        "JWT_SECRET_KEY",
        "OPENROUTER_API_KEY",
        "OPENAI_API_KEY",
        "JINA_API_KEY",
        "SENDGRID_API_KEY",
        "GOOGLE_CLIENT_SECRET",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "access_token",
        "refresh_token",
        "password",
    }
    leaked_keys = sorted(key for key in summary if key in forbidden_keys)
    if leaked_keys:
        return CheckResult("diagnostics secret redaction", "FAIL", f"Secret-bearing keys exposed: {', '.join(leaked_keys)}")
    return CheckResult("diagnostics secret redaction", "PASS", "Diagnostics summary exposes only secret-safe config")


def check_docs_disabled_in_production() -> CheckResult:
    main_py = _read("app/main.py")
    expected = 'docs_url="/docs" if settings.ENVIRONMENT != "production" else None'
    if expected in main_py:
        return CheckResult("production docs disabled", "PASS", "FastAPI docs are disabled when ENVIRONMENT=production")
    return CheckResult("production docs disabled", "FAIL", "Could not confirm production docs are disabled")


def check_env_example_placeholders() -> CheckResult:
    env_example = _read(".env.example")
    expected_markers = [
        "JWT_SECRET_KEY=change-me-to-a-random-256-bit-secret",
        "POSTGRES_PASSWORD=change-me-db-password",
        "MINIO_ACCESS_KEY=minioadmin",
        "MINIO_SECRET_KEY=minioadmin",
        "ENVIRONMENT=development",
    ]
    missing = [marker for marker in expected_markers if marker not in env_example]
    if missing:
        return CheckResult("env example placeholders", "FAIL", f"Missing expected demo placeholders: {', '.join(missing)}")
    return CheckResult("env example placeholders", "PASS", ".env.example keeps demo placeholders explicit")


def run_checks() -> list[CheckResult]:
    checks: list[Callable[[], CheckResult]] = [
        check_production_accepts_safe_settings,
        check_jwt_placeholder_rejected,
        check_wildcard_cors_rejected,
        check_default_minio_rejected,
        check_provider_keys_required,
        check_internal_ports_removed,
        check_flower_ops_profile,
        check_admin_diagnostics_auth,
        check_diagnostics_summary_safe,
        check_docs_disabled_in_production,
        check_env_example_placeholders,
    ]
    results: list[CheckResult] = []
    for check in checks:
        try:
            results.append(check())
        except Exception as exc:
            results.append(CheckResult(check.__name__, "FAIL", str(exc)))
    return results


def main() -> None:
    results = run_checks()
    print("Security readiness checks")
    print("=========================")
    for result in results:
        print(f"[{result.status}] {result.name}: {result.detail}")

    failed = [result for result in results if result.status != "PASS"]
    if failed:
        print(f"\n{len(failed)} check(s) failed.", file=sys.stderr)
        raise SystemExit(1)
    print("\nAll security readiness checks passed.")


if __name__ == "__main__":
    main()
