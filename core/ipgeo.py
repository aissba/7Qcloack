"""
IP geolocation via ipinfo.io (Bearer token auth).
Returns a normalised dict with country, country_code, isp/org.
"""
import requests
from config import IPINFO_API_TOKEN

_BASE = "https://ipinfo.io"
_TIMEOUT = 5


def lookup(ip: str) -> dict:
    """
    Returns:
        {
            "country":      "United States",
            "country_code": "US",
            "isp":          "AS15169 Google LLC",
            "org":          "AS15169 Google LLC",
            "query":        "8.8.8.8"
        }
    Empty dict on failure.
    """
    try:
        headers = {"Authorization": f"Bearer {IPINFO_API_TOKEN}"} if IPINFO_API_TOKEN else {}
        r = requests.get(f"{_BASE}/{ip}/json", headers=headers, timeout=_TIMEOUT)
        data = r.json()

        if "bogon" in data or "error" in data:
            return {}

        country_code = data.get("country", "")
        org = data.get("org", "")  # e.g. "AS15169 Google LLC"

        return {
            "country":      _country_name(country_code),
            "country_code": country_code,
            "isp":          org,
            "org":          org,
            "query":        data.get("ip", ip),
        }
    except Exception:
        return {}


# Minimal country-code → name map for display; falls back to code itself
_NAMES: dict[str, str] = {}

def _country_name(code: str) -> str:
    return _NAMES.get(code.upper(), code)
