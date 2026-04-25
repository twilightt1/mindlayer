import json

from app.api.v1.sse import format_sse, safe_json_dumps


def test_safe_json_dumps_preserves_unicode_and_compacts_json():
    payload = {"type": "token", "content": "Xin chào"}

    dumped = safe_json_dumps(payload)

    assert dumped == '{"type":"token","content":"Xin chào"}'


def test_format_sse_with_named_event():
    frame = format_sse({"type": "status", "stage": "retrieval"}, event="status")

    assert frame == 'event: status\ndata: {"type":"status","stage":"retrieval"}\n\n'


def test_format_sse_without_named_event():
    frame = format_sse({"type": "done", "sources": []})

    assert frame == 'data: {"type":"done","sources":[]}\n\n'


def test_format_sse_data_line_is_valid_json():
    frame = format_sse({"type": "token", "content": "hello"}, event="token")
    data_line = next(line for line in frame.splitlines() if line.startswith("data: "))

    assert json.loads(data_line.removeprefix("data: ")) == {
        "type": "token",
        "content": "hello",
    }
