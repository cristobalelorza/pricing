"""SQLite database layer for Precio."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import bcrypt

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("SQLITE_PATH", str(BASE_DIR / "data" / "precio.db"))
FREE_CREDITS = int(os.getenv("FREE_CREDITS", "5"))

_conn: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _init_tables(_conn)
    return _conn


def _init_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            credits_remaining INTEGER NOT NULL DEFAULT 5,
            openrouter_key TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            runs_today INTEGER NOT NULL DEFAULT 0,
            runs_today_date TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS businesses (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            industry TEXT DEFAULT '',
            location TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS services (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            default_constraints TEXT DEFAULT '',
            estimated_hours REAL,
            hourly_rate REAL,
            normal_delivery_days INTEGER,
            fast_delivery_days INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS results (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            business_id TEXT DEFAULT '',
            filename TEXT NOT NULL,
            deal_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()

    # Add location column to businesses if missing (migration)
    try:
        conn.execute("ALTER TABLE businesses ADD COLUMN location TEXT DEFAULT ''")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists

    # Create default admin account if no users exist
    row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    if row[0] == 0:
        pw_hash = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO users (id, email, password_hash, credits_remaining, created_at) VALUES (?, ?, ?, ?, ?)",
            ("admin", "admin", pw_hash, 9999, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# === Users ===

def create_user(email: str, password: str) -> dict | None:
    """Create a new user. Returns user dict or None if email taken."""
    db = get_db()
    uid = new_id()
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        db.execute(
            "INSERT INTO users (id, email, password_hash, credits_remaining, created_at) VALUES (?, ?, ?, ?, ?)",
            (uid, email.lower().strip(), pw_hash, FREE_CREDITS, now_iso()),
        )
        db.commit()
        return get_user(uid)
    except sqlite3.IntegrityError:
        return None


def authenticate(email: str, password: str) -> dict | None:
    """Check credentials. Returns user dict or None."""
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
    if not row:
        return None
    if bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return dict(row)
    return None


def get_user(user_id: str) -> dict | None:
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def update_user_key(user_id: str, key: str):
    db = get_db()
    db.execute("UPDATE users SET openrouter_key = ? WHERE id = ?", (key, user_id))
    db.commit()


def use_credit(user_id: str) -> bool:
    """Decrement a credit. Returns False if no credits left and no own key."""
    db = get_db()
    user = get_user(user_id)
    if not user:
        return False

    # Check daily rate limit
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if user["runs_today_date"] == today:
        if user["runs_today"] >= 20:
            return False
        db.execute("UPDATE users SET runs_today = runs_today + 1 WHERE id = ?", (user_id,))
    else:
        db.execute("UPDATE users SET runs_today = 1, runs_today_date = ? WHERE id = ?", (today, user_id))

    # If user has own key, don't decrement credits
    if user["openrouter_key"]:
        db.commit()
        return True

    # Decrement credits
    if user["credits_remaining"] <= 0:
        db.commit()
        return False
    db.execute("UPDATE users SET credits_remaining = credits_remaining - 1 WHERE id = ?", (user_id,))
    db.commit()
    return True


def get_user_api_key(user_id: str) -> str:
    """Return user's own key if set, otherwise the server default."""
    user = get_user(user_id)
    if user and user["openrouter_key"]:
        return user["openrouter_key"]
    return os.getenv("OPENROUTER_API_KEY", "")


# === Businesses (user-scoped) ===

def list_businesses(user_id: str = "") -> list[dict]:
    """List all businesses (shared across all users)."""
    db = get_db()
    rows = db.execute("SELECT * FROM businesses ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def get_business(user_id: str, biz_id: str) -> dict | None:
    """Get a business by ID (shared, no user filter)."""
    db = get_db()
    row = db.execute("SELECT * FROM businesses WHERE id = ?", (biz_id,)).fetchone()
    return dict(row) if row else None


def save_business(user_id: str, biz_id: str | None, name: str, url: str, industry: str = "", notes: str = "", location: str = "") -> dict:
    db = get_db()
    if biz_id:
        db.execute("UPDATE businesses SET name=?, url=?, industry=?, location=?, notes=? WHERE id=?",
                   (name, url, industry, location, notes, biz_id))
    else:
        biz_id = new_id()
        db.execute("INSERT INTO businesses (id, user_id, name, url, industry, location, notes, created_at) VALUES (?,?,?,?,?,?,?,?)",
                   (biz_id, user_id, name, url, industry, location, notes, now_iso()))
    db.commit()
    return get_business(user_id, biz_id)


def delete_business(user_id: str, biz_id: str):
    db = get_db()
    db.execute("DELETE FROM businesses WHERE id = ?", (biz_id,))
    db.commit()


# === Services (user-scoped) ===

def list_services(user_id: str = "") -> list[dict]:
    """List all services (shared across all users)."""
    db = get_db()
    rows = db.execute("SELECT * FROM services ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def get_service(user_id: str, svc_id: str) -> dict | None:
    """Get a service by ID (shared, no user filter)."""
    db = get_db()
    row = db.execute("SELECT * FROM services WHERE id = ?", (svc_id,)).fetchone()
    return dict(row) if row else None


def save_service(user_id: str, svc_id: str | None, **fields) -> dict:
    db = get_db()
    if svc_id:
        sets = ", ".join(f"{k}=?" for k in fields)
        db.execute(f"UPDATE services SET {sets} WHERE id=? AND user_id=?",
                   (*fields.values(), svc_id, user_id))
    else:
        svc_id = new_id()
        fields["id"] = svc_id
        fields["user_id"] = user_id
        fields["created_at"] = now_iso()
        cols = ", ".join(fields.keys())
        placeholders = ", ".join("?" for _ in fields)
        db.execute(f"INSERT INTO services ({cols}) VALUES ({placeholders})", tuple(fields.values()))
    db.commit()
    return get_service(user_id, svc_id)


def delete_service(user_id: str, svc_id: str):
    db = get_db()
    db.execute("DELETE FROM services WHERE id = ?", (svc_id,))
    db.commit()


# === Results (user-scoped) ===

def save_result(user_id: str, business_id: str, filename: str, deal_json: str, result_json: str) -> str:
    db = get_db()
    rid = new_id()
    db.execute(
        "INSERT INTO results (id, user_id, business_id, filename, deal_json, result_json, created_at) VALUES (?,?,?,?,?,?,?)",
        (rid, user_id, business_id, filename, deal_json, result_json, now_iso()),
    )
    db.commit()
    return rid


def list_results(user_id: str, search: str = "", currency: str = "") -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM results WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    results = []
    search_lower = search.lower()
    for row in rows:
        try:
            deal = json.loads(row["deal_json"])
            result = json.loads(row["result_json"])
            url = deal.get("business_url", "")
            service = deal.get("service_description", "")[:80]
            cur = result.get("currency", "USD")
            if search_lower and search_lower not in url.lower() and search_lower not in service.lower():
                continue
            if currency and cur != currency:
                continue
            results.append({
                "filename": row["filename"],
                "timestamp": row["created_at"],
                "url": url,
                "service": service,
                "floor": result.get("price_floor", 0),
                "target": result.get("price_target", 0),
                "stretch": result.get("price_stretch", 0),
                "currency": cur,
                "valid": result.get("validation", {}).get("is_valid") if result.get("validation") else None,
                "note": row["note"] or "",
            })
        except (json.JSONDecodeError, Exception):
            continue
    return results


def get_result(user_id: str, filename: str) -> dict | None:
    db = get_db()
    row = db.execute("SELECT * FROM results WHERE filename = ? AND user_id = ?", (filename, user_id)).fetchone()
    if not row:
        return None
    return dict(row)


def add_note_to_result(user_id: str, filename: str, note: str):
    db = get_db()
    db.execute("UPDATE results SET note = ? WHERE filename = ? AND user_id = ?", (note, filename, user_id))
    db.commit()


def get_business_results(user_id: str, business_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM results WHERE user_id = ? AND business_id = ? ORDER BY created_at DESC",
        (user_id, business_id),
    ).fetchall()
    results = []
    for row in rows:
        try:
            results.append({
                "filename": row["filename"],
                "timestamp": row["created_at"],
                "deal": json.loads(row["deal_json"]),
                "result": json.loads(row["result_json"]),
                "note": row["note"] or "",
            })
        except (json.JSONDecodeError, Exception):
            continue
    return results


def dashboard_stats(user_id: str) -> dict:
    db = get_db()
    biz_count = db.execute("SELECT COUNT(*) FROM businesses WHERE user_id = ?", (user_id,)).fetchone()[0]
    svc_count = db.execute("SELECT COUNT(*) FROM services WHERE user_id = ?", (user_id,)).fetchone()[0]
    run_count = db.execute("SELECT COUNT(*) FROM results WHERE user_id = ?", (user_id,)).fetchone()[0]

    # Recent results
    rows = db.execute(
        "SELECT * FROM results WHERE user_id = ? ORDER BY created_at DESC LIMIT 5", (user_id,)
    ).fetchall()
    recent = []
    targets = []
    for row in rows:
        try:
            result = json.loads(row["result_json"])
            deal = json.loads(row["deal_json"])
            t = result.get("price_target", 0)
            targets.append(t)
            recent.append({
                "filename": row["filename"],
                "timestamp": row["created_at"][:10],
                "url": deal.get("business_url", ""),
                "service": deal.get("service_description", "")[:60],
                "target": t,
                "currency": result.get("currency", "USD"),
                "valid": result.get("validation", {}).get("is_valid") if result.get("validation") else None,
                "note": row["note"] or "",
            })
        except (json.JSONDecodeError, Exception):
            continue

    avg_target = sum(targets) / len(targets) if targets else 0

    return {
        "total_businesses": biz_count,
        "total_services": svc_count,
        "total_runs": run_count,
        "avg_target": avg_target,
        "recent": recent,
    }
