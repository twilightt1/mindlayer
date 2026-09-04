"""Wiring tests for the agents (hub clients) router — CI-safe, no live DB."""
from __future__ import annotations

from fastapi.routing import APIRoute

from app.api.v1.agents import router


def test_agents_routes_registered():
    paths = {route.path for route in router.routes if isinstance(route, APIRoute)}
    assert "/agents" in paths
    assert "/agents/access-log" in paths
    assert "/agents/{client_id}" in paths


def test_agents_no_token_field_in_list_response():
    from app.schemas.Orivory import AgentClientResponse

    assert "token" not in AgentClientResponse.model_fields
