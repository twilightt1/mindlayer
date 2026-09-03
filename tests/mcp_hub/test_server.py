"""Minimal wiring tests for the MCP server module (import-only, no network)."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.mcp_hub.server import build_mcp_server, get_mcp_app


def test_build_mcp_server_returns_named_fastmcp():
    server = build_mcp_server()
    assert isinstance(server, FastMCP)
    assert server.name == "orivory-memory"
    assert server.settings.stateless_http is True
    assert server.settings.json_response is True


def test_get_mcp_app_returns_asgi_app():
    app = get_mcp_app()
    assert callable(app)
