"""SSRF protection for user-supplied URLs.

User-configurable connectors (RSS, web clipper) fetch arbitrary URLs. Without
guards, a user can point a source at cloud metadata endpoints
(169.254.169.254), localhost services, or RFC1918 addresses and read the
responses back as Memories — a full read-SSRF primitive.

Guards here:
- scheme allowlist (http/https)
- hostname resolution against private/loopback/link-local/CGNAT ranges (v4+6)
- response-size cap enforced while reading the body
- post-redirect IP re-validation (via httpx event hooks)
"""
from __future__ import annotations

import ipaddress
import logging
import socket
from urllib.parse import urlparse

import httpx

log = logging.getLogger(__name__)

MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB per fetch


class SSRFBlockedError(ValueError):
    """Raised when a URL targets a disallowed host."""


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
        or ip in ipaddress.ip_network("100.64.0.0/10")  # CGNAT
        or (getattr(ip, "ipv4_mapped", None) and ip.ipv4_mapped and _is_blocked_ip(ip.ipv4_mapped))
    )


def resolve_and_validate_url(url: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Validate scheme and resolve the hostname, blocking private targets.

    Returns the resolved IP list. Raises SSRFBlockedError otherwise.
    """
    try:
        parsed = urlparse(url)
    except (ValueError, TypeError) as exc:
        raise SSRFBlockedError(f"Unparseable URL: {url!r}") from exc

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise SSRFBlockedError("Only http(s) URLs are allowed")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFBlockedError("URL has no hostname")

    # Literal IPs are validated directly.
    try:
        literal = ipaddress.ip_address(hostname)
        if _is_blocked_ip(literal):
            raise SSRFBlockedError(f"Blocked IP literal: {hostname}")
        return [literal]
    except ValueError:
        pass  # hostname, not a literal IP

    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise SSRFBlockedError(f"DNS resolution failed for {hostname}") from exc

    if not infos:
        raise SSRFBlockedError(f"No DNS records for {hostname}")

    resolved: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if _is_blocked_ip(ip):
            raise SSRFBlockedError(f"Blocked resolved address: {addr}")
        resolved.append(ip)
    return resolved


def validate_url(url: str) -> str:
    """Public guard: raise SSRFBlockedError unless the URL is fetchable."""
    resolve_and_validate_url(url)
    return url


async def fetch_guarded(
    client: httpx.AsyncClient,
    url: str,
    *,
    method: str = "GET",
    max_bytes: int = MAX_RESPONSE_BYTES,
    max_redirects: int = 5,
    **kwargs,
) -> httpx.Response:
    """Fetch a URL with SSRF guards and a hard response-size cap.

    Redirects are followed MANUALLY so every hop's target URL is
    re-resolved and re-validated against the blocklist — a public URL that
    302s to 169.254.169.254 is caught. The response body is read in chunks;
    anything beyond ``max_bytes`` aborts the read rather than buffering a
    multi-GB body into memory.
    """
    kwargs.pop("follow_redirects", None)

    current_url = url
    for _ in range(max_redirects + 1):
        validate_url(current_url)
        request = client.build_request(method, current_url, **kwargs)
        response = await client.send(request, stream=True)
        if response.is_redirect:
            location = response.headers.get("location", "")
            await response.aclose()
            if not location:
                raise SSRFBlockedError("Redirect without Location header")
            current_url = str(response.url.join(location))
            continue
        break

    try:
        content_length = response.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > max_bytes:
            raise SSRFBlockedError(
                f"Response too large ({content_length} bytes > {max_bytes})"
            )
        chunks: list[bytes] = []
        total = 0
        async for chunk in response.aiter_bytes():
            total += len(chunk)
            if total > max_bytes:
                break
            chunks.append(chunk)
        await response.aclose()
    except SSRFBlockedError:
        await response.aclose()
        raise
    except Exception:
        await response.aclose()
        raise

    body = b"".join(chunks)
    response.read = lambda: body  # type: ignore[method-assign]
    # Ensure stream=True bookkeeping doesn't leak: response already closed.
    response.is_closed = True
    return response
