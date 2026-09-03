"""Minimal wiring tests for the MCP server module (import-only, no network)."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from starlette._utils import get_route_path

from app.mcp_hub.server import build_mcp_server, get_mcp_app, normalize_mcp_scope


def test_build_mcp_server_returns_named_fastmcp():
    server = build_mcp_server()
    assert isinstance(server, FastMCP)
    assert server.name == "orivory-memory"
    assert server.settings.stateless_http is True
    assert server.settings.json_response is True


def test_get_mcp_app_returns_asgi_app():
    app = get_mcp_app()
    assert callable(app)


def test_normalize_scope_exact_root_matches_inner_route():
    """Exact-route invocation (path=/mcp, no root_path): the SDK's inner ``Route("/")``
    must see ``/`` after the rewrite, without the 307 that would strip Authorization."""
    scope = {"type": "http", "path": "/mcp", "root_path": ""}
    normalize_mcp_scope(scope)
    assert get_route_path(scope) == "/"


def test_normalize_scope_mount_root_matches_inner_route():
    """Mount invocation (root_path=/mcp): the SDK's inner ``Route("/")`` must see ``/``."""
    scope = {"type": "http", "path": "/mcp", "root_path": "/mcp"}
    normalize_mcp_scope(scope)
    assert scope["path"] == "/mcp/"
    assert get_route_path(scope) == "/"


def test_normalize_scope_proxy_root_matches_inner_route():
    """Proxy-style root (root_path=/api): the rewrite keeps the prefix so the inner
    route still resolves to ``/`` — root_path is stripped by ``get_route_path``."""
    scope = {"type": "http", "path": "/api/mcp", "root_path": "/api"}
    normalize_mcp_scope(scope)
    assert get_route_path(scope) == "/"
