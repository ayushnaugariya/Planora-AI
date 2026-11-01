"""Explicit proxy trust; the ASGI server must preserve the socket peer."""

import ipaddress
from collections.abc import Mapping
from typing import Self

from starlette.types import ASGIApp, Receive, Scope, Send


def address(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """Accept bare IP literals only; normalize IPv4-mapped IPv6 quota keys."""
    if "%" in value:
        raise ValueError("Scoped addresses are not supported")
    result = ipaddress.ip_address(value)
    if isinstance(result, ipaddress.IPv6Address):
        return result.ipv4_mapped or result
    return result


class ProxyPolicy:
    def __init__(self, cidrs: str = "") -> None:
        if len(cidrs) > 4096 or "%" in cidrs:
            raise ValueError("TRUSTED_PROXY_CIDRS is too long or contains a scoped address")
        entries = cidrs.split(",") if cidrs.strip() else []
        if len(entries) > 32:
            raise ValueError("TRUSTED_PROXY_CIDRS allows at most 32 networks")
        try:
            self.networks = tuple(ipaddress.ip_network(item.strip()) for item in entries)
        except ValueError as exc:
            raise ValueError(
                "TRUSTED_PROXY_CIDRS must contain explicit IP addresses or canonical CIDRs"
            ) from exc
        if any(net.prefixlen == 0 for net in self.networks):
            raise ValueError("TRUSTED_PROXY_CIDRS cannot trust every address")

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> Self:
        if env.get("TRUST_PROXY", "0") not in ("", "0"):
            raise ValueError("Remove TRUST_PROXY; configure explicit TRUSTED_PROXY_CIDRS instead")
        return cls(env.get("TRUSTED_PROXY_CIDRS", ""))

    def trusted(self, host: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        return any(host in network for network in self.networks)

    def resolve(self, scope: Scope) -> tuple[str, str]:
        scheme = scope["scheme"]
        try:
            peer = address(scope["client"][0])
        except (ValueError, TypeError, KeyError, IndexError):
            return "unknown", scheme
        if not self.trusted(peer):
            return str(peer), scheme

        headers = scope.get("headers", [])
        forwarded = [value for name, value in headers if name.lower() == b"x-forwarded-for"]
        protos = [value for name, value in headers if name.lower() == b"x-forwarded-proto"]
        # A configured proxy must overwrite Proto, not append a client value.
        if len(protos) == 1 and protos[0] in (b"http", b"https"):
            scheme = protos[0].decode("ascii")
        if len(forwarded) != 1 or len(forwarded[0]) > 2048:
            return str(peer), scheme
        tokens = forwarded[0].split(b",")
        if len(tokens) > 32:
            return str(peer), scheme
        try:
            chain = [address(token.decode("ascii").strip(" \t")) for token in tokens]
        except (ValueError, UnicodeError):
            return str(peer), scheme
        # Stop at the nearest untrusted hop. Anything to its left is untrusted
        # input, even if it happens to look like an allowed proxy address.
        for hop in reversed(chain):
            if not self.trusted(hop):
                return str(hop), scheme
        # An all-trusted/ambiguous chain is not evidence of a distinct client.
        return str(peer), scheme


class TrustedProxyMiddleware:
    def __init__(self, app: ASGIApp, policy: ProxyPolicy) -> None:
        self.app = app
        self.policy = policy

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            host, scheme = self.policy.resolve(scope)
            scope = {**scope, "client": (host, 0), "scheme": scheme}
        await self.app(scope, receive, send)
