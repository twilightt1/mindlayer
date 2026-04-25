import pytest

from eval.live_api_eval import (
    CollectedSseResponse,
    LiveApiEvalError,
    SseEvent,
    collect_sse_response,
    infer_correction_count,
    normalize_source_filenames,
    parse_sse_stream,
    score_live_response,
)

pytestmark = pytest.mark.eval


def test_parse_sse_stream_handles_named_events():
    stream = "\n\n".join(
        [
            'event: status\ndata: {"type":"status","stage":"started"}',
            'event: token\ndata: {"type":"token","content":"Hello"}',
            'event: token\ndata: {"type":"token","content":" world"}',
            'event: sources\ndata: {"type":"sources","sources":[{"filename":"guide.md"}]}',
            'event: trace\ndata: {"type":"trace","agent_trace":{"correction":[]}}',
            'event: done\ndata: {"type":"done","retry_count":0}',
        ]
    )

    events = parse_sse_stream(stream)

    assert [event.event for event in events] == [
        "status",
        "token",
        "token",
        "sources",
        "trace",
        "done",
    ]
    assert events[1].data["content"] == "Hello"


def test_collect_sse_response_aggregates_tokens_sources_trace_and_done():
    events = [
        SseEvent("status", {"type": "status", "stage": "answer"}),
        SseEvent("token", {"type": "token", "content": "Hello"}),
        SseEvent("token", {"type": "token", "content": " world"}),
        SseEvent("sources", {"type": "sources", "sources": [{"filename": "guide.md"}]}),
        SseEvent("trace", {"type": "trace", "agent_trace": {"correction": {"reason": "retry"}}}),
        SseEvent("done", {"type": "done", "retry_count": 1}),
    ]

    response = collect_sse_response(events)

    assert response.answer == "Hello world"
    assert response.sources == [{"filename": "guide.md"}]
    assert response.trace == {"correction": {"reason": "retry"}}
    assert response.statuses == [{"type": "status", "stage": "answer"}]
    assert response.done == {"type": "done", "retry_count": 1}


def test_collect_sse_response_raises_on_error_event():
    with pytest.raises(LiveApiEvalError, match="boom"):
        collect_sse_response([SseEvent("error", {"type": "error", "message": "boom"})])


def test_normalize_source_filenames_strips_paths():
    sources = [
        {"filename": "api_authentication_guide.md"},
        {"filename": "nested/path/billing_and_plans_faq.md"},
        {"filename": ""},
    ]

    assert normalize_source_filenames(sources) == [
        "api_authentication_guide.md",
        "billing_and_plans_faq.md",
    ]


def test_infer_correction_count_uses_trace_and_done_retry_count():
    assert infer_correction_count({"correction": [{"reason": "hallucination"}]}, {"retry_count": 0}) == 1
    assert infer_correction_count({}, {"retry_count": 2}) == 2


def test_score_live_response_computes_metrics_from_mock_response():
    item = {
        "id": "api_auth_001",
        "query": "How do I rotate an API key?",
        "category": "api_auth",
        "expected_sources": ["api_authentication_guide.md"],
        "expected_keywords": ["rotate", "API key", "Settings", "Developer"],
        "should_fallback": False,
    }
    response = CollectedSseResponse(
        answer="Use Settings > Developer to rotate an API key. [Source 1]",
        sources=[
            {
                "filename": "api_authentication_guide.md",
                "content": "Settings Developer rotate API key",
            }
        ],
        trace={"correction": []},
        statuses=[],
        done={"retry_count": 0},
        raw_events=[],
    )

    result = score_live_response(item, response, latency_ms=42.0)

    assert result["source_hit"] == 1.0
    assert result["keyword_coverage"] == 1.0
    assert result["fallback_accuracy"] == 1.0
    assert result["has_citation"] is True
    assert result["latency_ms"] == 42.0
    assert result["passed"] is True
