import ipaddress
import urllib.parse
from typing import Optional

class SSRFSecurityException(Exception):
    pass

class SSRFGuard:
    """
    Part 13 / Part 15: SSRF Defense & Endpoint Validator.
    Prevents requests to localhost, loopback, private IPv4/IPv6 networks,
    and cloud metadata services (e.g., 169.254.169.254).
    """

    BLOCKED_HOSTS = {"localhost", "127.0.0.1", "::1", "metadata.google.internal"}

    @classmethod
    def validate_url(cls, url: str) -> str:
        """
        Validates an external GIS endpoint URL.
        Raises SSRFSecurityException if destination is internal or private.
        """
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise SSRFSecurityException(f"Unsupported URL protocol '{parsed.scheme}'. Only HTTP/HTTPS permitted.")

        hostname = parsed.hostname
        if not hostname:
            raise SSRFSecurityException("URL must contain a valid hostname.")

        # Check blocked hostnames
        if hostname.lower() in cls.BLOCKED_HOSTS:
            raise SSRFSecurityException(f"Blocked internal/loopback host: {hostname}")

        # Check IP address ranges
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise SSRFSecurityException(f"Blocked private/internal IP address: {hostname}")
            # Cloud metadata range 169.254.0.0/16
            if ip in ipaddress.ip_network("169.254.0.0/16"):
                raise SSRFSecurityException("Blocked cloud instance metadata IP address.")
        except ValueError:
            # Hostname is a domain name (not a raw IP), check for local domain patterns
            if hostname.endswith(".local") or hostname.endswith(".internal") or hostname.endswith(".localhost"):
                raise SSRFSecurityException(f"Blocked internal domain suffix: {hostname}")

        return url
