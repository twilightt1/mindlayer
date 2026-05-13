from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_DOCS = [
    ROOT / "sample_docs" / "api_authentication_guide.md",
    ROOT / "sample_docs" / "billing_and_plans_faq.md",
    ROOT / "sample_docs" / "webhook_troubleshooting.md",
]
DEFAULT_QUESTIONS = [
    "How do I rotate an API key?",
    "Which plan supports SSO?",
    "What are the webhook retry rules?",
]
READY_STATUSES = {"ready"}
FAILED_STATUSES = {"failed"}


class SmokeFailure(RuntimeError):
    """Raised when the demo smoke workflow cannot complete successfully."""


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _print_step(message: str) -> None:
    print(f"\n==> {message}")


def _print_ok(message: str) -> None:
    print(f"    OK: {message}")


def _parse_doc_paths(values: list[str] | None) -> list[Path]:
    if not values:
        return DEFAULT_DOCS
    return [Path(value).resolve() for value in values]


def _load_questions(values: list[str] | None) -> list[str]:
    return values or DEFAULT_QUESTIONS


async def ensure_demo_user(email: str, password: str, display_name: str) -> None:
    """Create or normalize a local demo user so the smoke can log in by API."""
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.models.user_quota import UserQuota
    from app.services.auth_service import _hash

    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == email))
        quota = None
        if user:
            user.hashed_password = _hash(password)
            user.auth_provider = "email"
            user.display_name = display_name
            user.is_verified = True
            user.onboarding_done = True
            user.is_active = True
            user.is_deleted = False
            quota = await db.scalar(select(UserQuota).where(UserQuota.user_id == user.id))
        else:
            user = User(
                email=email,
                hashed_password=_hash(password),
                display_name=display_name,
                auth_provider="email",
                is_verified=True,
                onboarding_done=True,
                is_active=True,
                is_deleted=False,
            )
            db.add(user)
            await db.flush()
        if not quota:
            db.add(UserQuota(user_id=user.id))
        await db.commit()


async def check_endpoint(client: httpx.AsyncClient, path: str) -> dict[str, Any]:
    response = await client.get(path)
    response.raise_for_status()
    return response.json()


async def login(client: httpx.AsyncClient, email: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise SmokeFailure("Login response did not include access_token")
    return token


async def create_conversation(client: httpx.AsyncClient, token: str, title: str) -> str:
    response = await client.post(
        "/api/v1/chat/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": title},
    )
    response.raise_for_status()
    conversation_id = response.json().get("id")
    if not conversation_id:
        raise SmokeFailure("Create conversation response did not include id")
    return conversation_id


async def upload_document(
    client: httpx.AsyncClient,
    token: str,
    conversation_id: str,
    path: Path,
) -> str:
    if not path.exists():
        raise SmokeFailure(f"Sample document not found: {path}")

    with path.open("rb") as handle:
        response = await client.post(
            f"/api/v1/chat/conversations/{conversation_id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (path.name, handle, "text/plain")},
        )
    response.raise_for_status()
    document_id = response.json().get("id")
    if not document_id:
        raise SmokeFailure(f"Upload response did not include id for {path.name}")
    return document_id


async def get_document(
    client: httpx.AsyncClient,
    token: str,
    conversation_id: str,
    document_id: str,
) -> dict[str, Any]:
    response = await client.get(
        f"/api/v1/chat/conversations/{conversation_id}/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()


async def wait_for_documents(
    client: httpx.AsyncClient,
    token: str,
    conversation_id: str,
    document_ids: list[str],
    timeout_seconds: int,
    poll_interval: float,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    latest: dict[str, dict[str, Any]] = {}

    while time.monotonic() < deadline:
        all_ready = True
        for document_id in document_ids:
            doc = await get_document(client, token, conversation_id, document_id)
            latest[document_id] = doc
            status = doc.get("status")
            if status in FAILED_STATUSES:
                raise SmokeFailure(
                    f"Document {document_id} failed ingestion: {doc.get('error_msg')}"
                )
            if status not in READY_STATUSES:
                all_ready = False
        if all_ready:
            return
        await asyncio.sleep(poll_interval)

    status_summary = {
        doc_id: {"status": doc.get("status"), "error_msg": doc.get("error_msg")}
        for doc_id, doc in latest.items()
    }
    raise SmokeFailure(
        "Timed out waiting for document ingestion: "
        f"{json.dumps(status_summary, ensure_ascii=False)}"
    )


def parse_sse_lines(lines: list[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    event_name = "message"
    data_lines: list[str] = []

    def flush() -> None:
        nonlocal event_name, data_lines
        if not data_lines:
            event_name = "message"
            return
        raw_data = "\n".join(data_lines)
        try:
            data: Any = json.loads(raw_data)
        except json.JSONDecodeError:
            data = raw_data
        events.append({"event": event_name, "data": data})
        event_name = "message"
        data_lines = []

    for line in lines:
        if not line:
            flush()
        elif line.startswith("event:"):
            event_name = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").strip())
    flush()
    return events


async def ask_question(
    client: httpx.AsyncClient,
    token: str,
    conversation_id: str,
    question: str,
) -> dict[str, Any]:
    lines: list[str] = []
    async with client.stream(
        "POST",
        f"/api/v1/chat/conversations/{conversation_id}/message",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"query": question},
        timeout=None,
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            lines.append(line)

    events = parse_sse_lines(lines)
    event_names = [event["event"] for event in events]
    if "error" in event_names:
        error_event = next(event for event in events if event["event"] == "error")
        raise SmokeFailure(f"SSE error for question {question!r}: {error_event['data']}")
    if "done" not in event_names:
        raise SmokeFailure(f"SSE stream did not emit done for question {question!r}")
    if "token" not in event_names:
        raise SmokeFailure(f"SSE stream did not emit token for question {question!r}")

    token_text = "".join(
        event["data"].get("content", "")
        for event in events
        if event["event"] == "token" and isinstance(event["data"], dict)
    ).strip()
    sources = []
    trace = {}
    for event in events:
        data = event["data"]
        if event["event"] == "sources" and isinstance(data, dict):
            sources = data.get("sources", [])
        if event["event"] == "trace" and isinstance(data, dict):
            trace = data.get("agent_trace", {})

    if not token_text:
        raise SmokeFailure(f"Empty answer for question {question!r}")
    if not sources:
        raise SmokeFailure(f"No sources returned for question {question!r}")
    if not trace:
        raise SmokeFailure(f"No agent trace returned for question {question!r}")

    return {
        "question": question,
        "answer_preview": token_text[:220],
        "event_names": event_names,
        "source_count": len(sources),
        "trace_keys": sorted(trace.keys()),
    }


async def run_smoke(args: argparse.Namespace) -> None:
    base_url = args.base_url.rstrip("/")
    docs = _parse_doc_paths(args.docs)
    questions = _load_questions(args.questions)
    title = f"MindLayer smoke {time.strftime('%Y-%m-%d %H:%M:%S')}"

    if args.seed_user:
        _print_step(f"Ensuring demo user exists: {args.email}")
        await ensure_demo_user(args.email, args.password, args.display_name)
        _print_ok("demo user is verified and onboarded")

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        _print_step("Checking API health")
        health = await check_endpoint(client, "/health")
        _print_ok(json.dumps(health, ensure_ascii=False))

        if not args.skip_ready:
            _print_step("Checking API readiness")
            ready = await check_endpoint(client, "/ready")
            _print_ok(json.dumps(ready, ensure_ascii=False))

        _print_step("Logging in through API")
        token = await login(client, args.email, args.password)
        _print_ok("received access token")

        _print_step("Creating demo conversation")
        conversation_id = await create_conversation(client, token, title)
        _print_ok(f"conversation_id={conversation_id}")

        _print_step(f"Uploading {len(docs)} sample document(s)")
        document_ids = []
        for path in docs:
            document_id = await upload_document(client, token, conversation_id, path)
            document_ids.append(document_id)
            _print_ok(f"{path.name} -> document_id={document_id}")

        _print_step("Waiting for ingestion to reach ready")
        await wait_for_documents(
            client,
            token,
            conversation_id,
            document_ids,
            timeout_seconds=args.ingestion_timeout,
            poll_interval=args.poll_interval,
        )
        _print_ok("all documents are ready")

        _print_step(f"Asking {len(questions)} RAG question(s) via SSE")
        results = []
        for question in questions:
            result = await ask_question(client, token, conversation_id, question)
            results.append(result)
            _print_ok(
                f"{question} | sources={result['source_count']} | "
                f"events={','.join(result['event_names'])}"
            )

    print("\n=== Demo smoke summary ===")
    print(json.dumps({"conversation_id": conversation_id, "results": results}, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a production-like MindLayer Demo smoke workflow.",
    )
    parser.add_argument("--base-url", default=_env("DEMO_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--email", default=_env("DEMO_USER_EMAIL", "mindlayer-demo@example.com"))
    parser.add_argument("--password", default=_env("DEMO_USER_PASSWORD", "DemoPassword123!"))
    parser.add_argument("--display-name", default=_env("DEMO_DISPLAY_NAME", "MindLayer Demo"))
    parser.add_argument("--doc", dest="docs", action="append", help="Document path to upload. Repeatable.")
    parser.add_argument("--question", dest="questions", action="append", help="Question to ask. Repeatable.")
    parser.add_argument("--ingestion-timeout", type=int, default=int(_env("DEMO_INGESTION_TIMEOUT", "180")))
    parser.add_argument("--poll-interval", type=float, default=float(_env("DEMO_POLL_INTERVAL", "2")))
    parser.add_argument("--skip-ready", action="store_true", help="Skip /ready dependency check.")
    parser.add_argument(
        "--no-seed-user",
        dest="seed_user",
        action="store_false",
        help="Do not create/update the local demo user before login.",
    )
    parser.set_defaults(seed_user=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        asyncio.run(run_smoke(args))
    except (httpx.HTTPError, SmokeFailure) as exc:
        print(f"\nDemo smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
