"""Tests for SSRF guards (app/utils/ssrf.py)."""
import ipaddress
from unittest.mock import MagicMock

import httpx
import pytest

from app.utils.ssrf import (
    MAX_RESPONSE_BYTES,
    SSRFBlockedError,
    fetch_guarded,
    validate_url,
)


def test_validate_blocks_private_literals():
    for host in [
        "127.0.0.1",
        "10.0.0.5",
        "172.16.1.1",
        "192.168.1.10",
        "169.254.169.254",  # cloud metadata
        "100.64.0.1",  # CGNAT
        "0.0.0.0",
        "::1",
        "fe80::1",
    ]:
        with pytest.raises(SSRFBlockedError):
            validate_url(f"http://{host}/x")


def test_validate_blocks_non_http_schemes():
    for scheme in ["file", "ftp", "gopher", "dict"]:
        with pytest.raises(SSRFBlockedError):
            validate_url(f"{scheme}://example.com/x")


def test_validate_blocks_unresolvable_and_public_ok(monkeypatch):
    import socket as socket_mod

    def fake_getaddrinfo(host, *args, **kwargs):
        if host == "internal.corp":
            return [(socket_mod.AF_INET, None, None, "", ("10.1.2.3", 0))]
        if host == "example.com":
            return [(socket_mod.AF_INET, None, None, "", ("93.184.216.34", 0))]
        raise socket_mod.gaierror(-2, "Name or service not known")

    monkeypatch.setattr(socket_mod, "getaddrinfo", fake_getaddrinfo)

    with pytest.raises(SSRFBlockedError):
        validate_url("http://internal.corp/x")  # resolves into RFC1918

    with pytest.raises(SSRFBlockedError):
        validate_url("http://does-not-exist.invalid/x")

    assert validate_url("https://example.com/x") == "https://example.com/x"


def test_fetch_guarded_follows_redirect_and_revalidates(monkeypatch):
    """A public URL that redirects to a private address must be blocked."""
    import socket as socket_mod

    def fake_getaddrinfo(host, *args, **kwargs):
        if host == "public.example":
            return [(socket_mod.AF_INET, None, None, "", ("93.184.216.34", 0))]
        raise socket_mod.gaierror(-2, "no record")

    monkeypatch.setattr(socket_mod, "getaddrinfo", fake_getaddrinfo)

    class FakeResponse:
        def __init__(self, url: str, status: int, headers: dict | None = None):
            self.url = httpx.URL(url)
            self.status_code = status
            self.headers = httpx.Headers(headers or {})
            self.is_redirect = 300 <= status < 400 and "location" in (headers or {})
            self.is_closed = False

        async def aiter_bytes(self):
            yield b"secret payload"
            raise AssertionError("should not be read")

        async def aclose(self):
            self.is_closed = True

    calls = []

    async def fake_send(request, stream=False):
        calls.append(str(request.url))
        if "public.example" in str(request.url):
            return FakeResponse(str(request.url), 302, {"location": "http://169.254.169.254/latest/meta-data/"})
        return FakeResponse(str(request.url), 200)

    client = MagicMock(spec=httpx.AsyncClient)
    client.build_request = lambda method, url, **kw: httpx.Request(method, url)
    client.send = fake_send

    # The redirect target is validated BEFORE the second request is sent,
    # so only one request is ever made.
    import asyncio

    async def run():
        with pytest.raises(SSRFBlockedError):
            await fetch_guarded(client, "https://public.example/a")

    asyncio.run(run())
    assert len(calls) == 1  # redirect target blocked pre-flight


def test_fetch_guarded_caps_body_size(monkeypatch):
    big = b"x" * (MAX_RESPONSE_BYTES + 100)

    class FakeResponse:
        def __init__(self):
            self.url = httpx.URL("https://example.com/big")
            self.status_code = 200
            self.headers = httpx.Headers({})
            self.is_redirect = False
            self.is_closed = False
            self._sent = False

        async def aiter_bytes(self):
            for i in range(0, len(big), 8192):
                yield big[i : i + 8192]

        async def aclose(self):
            self.is_closed = True

    async def fake_send(request, stream=False):
        return FakeResponse()

    client = MagicMock(spec=httpx.AsyncClient)
    client.build_request = lambda method, url, **kw: httpx.Request(method, url)
    client.send = fake_send

    import asyncio

    async def run():
        resp = await fetch_guarded(client, "https://example.com/big")
        return resp.read()

    body = asyncio.run(run())
    assert len(body) <= MAX_RESPONSE_BYTES


def test_ipv4_mapped_ipv6_blocked():
    from app.utils.ssrf import _is_blocked_ip

    assert _is_blocked_ip(ipaddress.ip_address("::ffff:127.0.0.1"))
    assert not _is_blocked_ip(ipaddress.ip_address("93.184.216.34"))
