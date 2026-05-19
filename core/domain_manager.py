"""
High-level domain + token management used by bot handlers.
Wraps db.models so handlers never import db directly.
"""
from db.models import (
    domain_add, domain_remove, domain_list, domain_get, domain_update,
    link_create, link_revoke_all, link_list,
)


# ── Domain helpers ─────────────────────────────────────────────────────────────

def add_domain(domain: str) -> bool:
    return domain_add(domain.lower())


def remove_domain(domain: str) -> bool:
    return domain_remove(domain.lower())


def get_all_domains():
    return domain_list()


def get_domain(domain: str):
    return domain_get(domain.lower())


def require_domain(domain: str):
    """Return domain row or raise ValueError."""
    row = domain_get(domain.lower())
    if not row:
        raise ValueError(f"Domain `{domain}` not found. Add it first with /adddomain.")
    return row


def set_safe_url(domain: str, url: str) -> bool:
    return domain_update(domain.lower(), safe_url=url)


def set_money_url(domain: str, url: str) -> bool:
    return domain_update(domain.lower(), money_url=url)


def set_countries(domain: str, countries: str) -> bool:
    return domain_update(domain.lower(), countries=countries.upper())


def set_threshold(domain: str, value: int) -> bool:
    return domain_update(domain.lower(), threshold=value)


def add_blocked_isp(domain: str, isp_name: str) -> bool:
    row = domain_get(domain.lower())
    if not row:
        return False
    existing = [x.strip() for x in (row["blocked_isps"] or "").split("|") if x.strip()]
    if isp_name not in existing:
        existing.append(isp_name)
    return domain_update(domain.lower(), blocked_isps="|".join(existing))


def set_notify_group(domain: str, group_id: str) -> bool:
    return domain_update(domain.lower(), notify_group=group_id)


def set_notify_enabled(domain: str, enabled: bool) -> bool:
    return domain_update(domain.lower(), notify_enabled=int(enabled))


def set_notify_level(domain: str, level: str) -> bool:
    return domain_update(domain.lower(), notify_level=level)


def set_device_filter(domain: str, device_filter: str) -> bool:
    return domain_update(domain.lower(), device_filter=device_filter)


# ── Token helpers ──────────────────────────────────────────────────────────────

def generate_token(domain: str) -> str:
    return link_create(domain.lower())


def regenerate_token(domain: str) -> str:
    link_revoke_all(domain.lower())
    return link_create(domain.lower())


def get_active_links(domain: str):
    return link_list(domain.lower())


def token_url(domain: str, token: str) -> str:
    return f"https://{domain}/go/{token}"
