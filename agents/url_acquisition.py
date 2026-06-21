"""Validacion defensiva de URLs publicas para PEC Auditor."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse


class URLAcquisitionAgent:
    """Acepta solo destinos HTTP(S) que no resuelvan a redes privadas."""

    def _host_is_public(self, host: str) -> bool:
        host = host.strip().lower().rstrip(".")
        if not host or host == "localhost" or host.endswith(".local"):
            return False
        try:
            address = ipaddress.ip_address(host)
            return self._address_is_public(address)
        except ValueError:
            pass

        try:
            resolved = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        except socket.gaierror:
            return False
        return bool(resolved) and all(
            self._address_is_public(ipaddress.ip_address(item[4][0])) for item in resolved
        )

    @staticmethod
    def _address_is_public(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        return address.is_global

    def validate_url(self, value: str) -> tuple[bool, str, str]:
        raw = (value or "").strip()
        parsed = urlparse(raw)
        if parsed.scheme.lower() not in {"http", "https"}:
            return False, "", "La URL debe usar el esquema http o https."
        if parsed.username or parsed.password:
            return False, "", "La URL no debe incluir credenciales."
        if not parsed.hostname or not self._host_is_public(parsed.hostname):
            return False, "", "La URL debe apuntar a un dominio público; localhost y redes privadas no están permitidos."
        normalized = urlunparse((parsed.scheme.lower(), parsed.netloc, parsed.path or "/", "", parsed.query, ""))
        return True, normalized, ""

    def acquire(self, url: str) -> dict:
        valid, normalized, message = self.validate_url(url)
        return {"valid": valid, "url": normalized, "warning": message}
