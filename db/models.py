"""
Single source of truth for all database tables.
Uses raw SQLite via a thread-safe connection helper.
"""
import sqlite3
import secrets
import string
from contextlib import contextmanager
from config import DATABASE_URL

# Strip "sqlite:///" prefix if present
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
    """Add new columns to existing databases without breaking fresh installs."""
    existing = {row[1] for row in c.execute("PRAGMA table_info(domains)")}
    if "device_filter" not in existing:
        c.execute("ALTER TABLE domains ADD COLUMN device_filter TEXT DEFAULT 'all'")


def init_db():
    with get_conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS domains (
                domain          TEXT PRIMARY KEY,
                safe_url        TEXT,
                money_url       TEXT,
                countries       TEXT    DEFAULT '',
                threshold       INTEGER DEFAULT 75,
                blocked_isps    TEXT    DEFAULT '',
                notify_group    TEXT    DEFAULT '',
                notify_enabled  INTEGER DEFAULT 0,
                notify_level    TEXT    DEFAULT 'all',
                device_filter   TEXT    DEFAULT 'all',
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
            );


            CREATE TABLE IF NOT EXISTS links (
                token       TEXT PRIMARY KEY,
                domain      TEXT    NOT NULL,
                active      INTEGER DEFAULT 1,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(domain) REFERENCES domains(domain) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS visits (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                domain      TEXT,
                token       TEXT,
                ip          TEXT,
                country     TEXT,
                country_code TEXT,
                isp         TEXT,
                action      TEXT,
                proxy       INTEGER DEFAULT 0,
                device_type TEXT    DEFAULT '',
                os          TEXT    DEFAULT '',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        _migrate(c)


# ── Token helpers (used by domain_manager) ────────────────────────────────────

def _make_token(n: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


# ── Domain CRUD ───────────────────────────────────────────────────────────────

def domain_add(domain: str) -> bool:
    from config import DEFAULT_BLOCKED_ISPS
    default_isps = "|".join(DEFAULT_BLOCKED_ISPS)
    try:
        with get_conn() as c:
            c.execute(
                "INSERT INTO domains (domain, blocked_isps) VALUES (?, ?)",
                (domain, default_isps),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def domain_remove(domain: str) -> bool:
    with get_conn() as c:
        cur = c.execute("DELETE FROM domains WHERE domain = ?", (domain,))
        return cur.rowcount > 0


def domain_list():
    with get_conn() as c:
        return c.execute("SELECT * FROM domains ORDER BY domain").fetchall()


def domain_get(domain: str):
    with get_conn() as c:
        return c.execute("SELECT * FROM domains WHERE domain = ?", (domain,)).fetchone()


def domain_update(domain: str, **fields) -> bool:
    if not fields:
        return False
    cols = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [domain]
    with get_conn() as c:
        cur = c.execute(f"UPDATE domains SET {cols} WHERE domain = ?", vals)
        return cur.rowcount > 0


# ── Links CRUD ────────────────────────────────────────────────────────────────

def link_create(domain: str) -> str:
    token = _make_token()
    with get_conn() as c:
        c.execute("INSERT INTO links (token, domain) VALUES (?, ?)", (token, domain))
    return token


def link_revoke_all(domain: str):
    with get_conn() as c:
        c.execute("UPDATE links SET active = 0 WHERE domain = ?", (domain,))


def link_list(domain: str):
    with get_conn() as c:
        return c.execute(
            "SELECT token, created_at FROM links WHERE domain = ? AND active = 1 ORDER BY created_at DESC",
            (domain,),
        ).fetchall()


def link_get_domain(token: str):
    with get_conn() as c:
        row = c.execute(
            "SELECT domain FROM links WHERE token = ? AND active = 1", (token,)
        ).fetchone()
        return row["domain"] if row else None


# ── Visits ────────────────────────────────────────────────────────────────────

def visit_log(domain, token, ip, country, country_code, isp, action, proxy=0, device_type="", os=""):
    with get_conn() as c:
        c.execute(
            """INSERT INTO visits
               (domain, token, ip, country, country_code, isp, action, proxy, device_type, os)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (domain, token, ip, country, country_code, isp, action, int(proxy), device_type, os),
        )


def visit_logs(domain: str, limit: int = 20):
    with get_conn() as c:
        return c.execute(
            "SELECT * FROM visits WHERE domain = ? ORDER BY created_at DESC LIMIT ?",
            (domain, limit),
        ).fetchall()


def visit_stats(domain: str) -> dict:
    with get_conn() as c:
        total = c.execute("SELECT COUNT(*) FROM visits WHERE domain = ?", (domain,)).fetchone()[0]
        money = c.execute(
            "SELECT COUNT(*) FROM visits WHERE domain = ? AND action = 'money'", (domain,)
        ).fetchone()[0]
        safe = c.execute(
            "SELECT COUNT(*) FROM visits WHERE domain = ? AND action = 'safe'", (domain,)
        ).fetchone()[0]
    return {"total": total, "money": money, "safe": safe}
