"""
Proxy / VPN / TOR detection via proxycheck.io v2 API.

Parameters used:
  vpn=1   → detect both proxies and VPNs
  asn=1   → include provider/ASN info
  risk=1  → include risk score (0-100)

Returns a dict so flow_engine can log extra detail,
or a simple bool via is_proxy().
"""
import requests
from config import PROXYCHECK_API_KEY

_BASE    = "https://proxycheck.io/v2"
_TIMEOUT = 5


def check(ip: str) -> dict:
    """
    Full result dict:
    {
        "proxy":      True | False,
        "type":       "VPN" | "SOCKS5" | "TOR" | "" | ...,
        "risk":       0-100,
        "provider":   "Amazon Web Services",
        "asn":        "AS16509",
    }
    Returns empty dict on API failure.
    """
    if not PROXYCHECK_API_KEY:
        return {}
    try:
        r = requests.get(
            f"{_BASE}/{ip}",
            params={
                "key": PROXYCHECK_API_KEY,
                "vpn": 1,
                "asn": 1,
                "risk": 1,
            },
            timeout=_TIMEOUT,
        )
        data = r.json()
        status = data.get("status", "")
        if status not in ("ok", "warning"):
            return {}

        ip_data = data.get(ip, {})
        proxy_flag = ip_data.get("proxy", "no") == "yes"

        return {
            "proxy":    proxy_flag,
            "type":     ip_data.get("type", ""),
            "risk":     int(ip_data.get("risk", 0)),
            "provider": ip_data.get("provider", ""),
            "asn":      ip_data.get("asn", ""),
        }
    except Exception:
        return {}


def is_proxy(ip: str) -> bool:
    """Convenience wrapper — returns True if IP is a proxy, VPN, or TOR node."""
    result = check(ip)
    return result.get("proxy", False)
