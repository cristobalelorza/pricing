"""Database layer for Precio. Uses Supabase (PostgreSQL) when configured, falls back to SQLite for local dev."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import bcrypt

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

FREE_CREDITS = int(os.getenv("FREE_CREDITS", "5"))

# --- Supabase client ---
_supabase = None


def _get_supabase():
    global _supabase
    if _supabase is None and USE_SUPABASE:
        from supabase import create_client
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


# --- SQLite fallback for local dev ---
_sqlite_conn = None
SQLITE_PATH = os.getenv("SQLITE_PATH", str(Path(__file__).resolve().parent.parent / "data" / "precio.db"))


def _get_sqlite():
    global _sqlite_conn
    if _sqlite_conn is None:
        Path(SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)
        _sqlite_conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
        _sqlite_conn.row_factory = sqlite3.Row
        _sqlite_conn.execute("PRAGMA journal_mode=WAL")
        _init_sqlite(_sqlite_conn)
    return _sqlite_conn


def _init_sqlite(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
            credits_remaining INTEGER NOT NULL DEFAULT 5, openrouter_key TEXT DEFAULT '',
            runs_today INTEGER NOT NULL DEFAULT 0, runs_today_date TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS businesses (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, name TEXT NOT NULL, url TEXT NOT NULL,
            industry TEXT DEFAULT '', location TEXT DEFAULT '', notes TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS services (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL,
            default_constraints TEXT DEFAULT '', estimated_hours REAL, hourly_rate REAL,
            normal_delivery_days INTEGER, fast_delivery_days INTEGER, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS results (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, business_id TEXT DEFAULT '',
            filename TEXT NOT NULL, deal_json TEXT NOT NULL, result_json TEXT NOT NULL,
            note TEXT DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, user_email TEXT NOT NULL,
            page_url TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'suggestion',
            message TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    try:
        conn.execute("ALTER TABLE businesses ADD COLUMN location TEXT DEFAULT ''")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    # Default admin
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        pw_hash = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()
        conn.execute("INSERT INTO users (id, email, password_hash, credits_remaining, created_at) VALUES (?, ?, ?, ?, ?)",
                     ("admin", "admin", pw_hash, 9999, now_iso()))
        conn.commit()


# --- Helpers ---
def new_id() -> str:
    return uuid.uuid4().hex[:12]

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# Unified API -- routes to Supabase or SQLite transparently
# ============================================================

# --- Users ---

def create_user(email: str, password: str) -> dict | None:
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    uid = new_id()
    if USE_SUPABASE:
        sb = _get_supabase()
        try:
            res = sb.table("users").insert({
                "id": uid, "email": email.lower().strip(), "password_hash": pw_hash,
                "credits_remaining": FREE_CREDITS, "created_at": now_iso(),
                "runs_today": 0, "runs_today_date": "", "openrouter_key": "",
            }).execute()
            return res.data[0] if res.data else None
        except Exception:
            return None
    else:
        db = _get_sqlite()
        try:
            db.execute("INSERT INTO users (id, email, password_hash, credits_remaining, created_at) VALUES (?,?,?,?,?)",
                       (uid, email.lower().strip(), pw_hash, FREE_CREDITS, now_iso()))
            db.commit()
            return get_user(uid)
        except sqlite3.IntegrityError:
            return None


def authenticate(email: str, password: str) -> dict | None:
    if USE_SUPABASE:
        sb = _get_supabase()
        res = sb.table("users").select("*").eq("email", email.lower().strip()).execute()
        if not res.data:
            return None
        user = res.data[0]
    else:
        db = _get_sqlite()
        row = db.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
        if not row:
            return None
        user = dict(row)
    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return user
    return None


def get_user(user_id: str) -> dict | None:
    if USE_SUPABASE:
        sb = _get_supabase()
        res = sb.table("users").select("*").eq("id", user_id).execute()
        return res.data[0] if res.data else None
    else:
        db = _get_sqlite()
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def update_user_key(user_id: str, key: str):
    if USE_SUPABASE:
        _get_supabase().table("users").update({"openrouter_key": key}).eq("id", user_id).execute()
    else:
        db = _get_sqlite()
        db.execute("UPDATE users SET openrouter_key = ? WHERE id = ?", (key, user_id))
        db.commit()


def use_credit(user_id: str) -> bool:
    user = get_user(user_id)
    if not user:
        return False
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if user["runs_today_date"] == today:
        if user["runs_today"] >= 20:
            return False
        new_runs = user["runs_today"] + 1
    else:
        new_runs = 1

    if USE_SUPABASE:
        sb = _get_supabase()
        update = {"runs_today": new_runs, "runs_today_date": today}
        if not user["openrouter_key"] and user["credits_remaining"] > 0:
            update["credits_remaining"] = user["credits_remaining"] - 1
        elif not user["openrouter_key"] and user["credits_remaining"] <= 0:
            return False
        sb.table("users").update(update).eq("id", user_id).execute()
    else:
        db = _get_sqlite()
        db.execute("UPDATE users SET runs_today = ?, runs_today_date = ? WHERE id = ?", (new_runs, today, user_id))
        if not user["openrouter_key"]:
            if user["credits_remaining"] <= 0:
                db.commit()
                return False
            db.execute("UPDATE users SET credits_remaining = credits_remaining - 1 WHERE id = ?", (user_id,))
        db.commit()
    return True


def get_user_api_key(user_id: str) -> str:
    user = get_user(user_id)
    if user and user["openrouter_key"]:
        return user["openrouter_key"]
    return os.getenv("OPENROUTER_API_KEY", "")


# --- Businesses (shared) ---

def list_businesses(user_id: str = "") -> list[dict]:
    if USE_SUPABASE:
        res = _get_supabase().table("businesses").select("*").order("name").execute()
        return res.data or []
    else:
        return [dict(r) for r in _get_sqlite().execute("SELECT * FROM businesses ORDER BY name").fetchall()]


def get_business(user_id: str, biz_id: str) -> dict | None:
    if USE_SUPABASE:
        res = _get_supabase().table("businesses").select("*").eq("id", biz_id).execute()
        return res.data[0] if res.data else None
    else:
        row = _get_sqlite().execute("SELECT * FROM businesses WHERE id = ?", (biz_id,)).fetchone()
        return dict(row) if row else None


def save_business(user_id: str, biz_id: str | None, name: str, url: str, industry: str = "", notes: str = "", location: str = "") -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        data = {"name": name, "url": url, "industry": industry, "location": location, "notes": notes}
        if biz_id:
            sb.table("businesses").update(data).eq("id", biz_id).execute()
        else:
            biz_id = new_id()
            data.update({"id": biz_id, "user_id": user_id, "created_at": now_iso()})
            sb.table("businesses").insert(data).execute()
    else:
        db = _get_sqlite()
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
    if USE_SUPABASE:
        _get_supabase().table("businesses").delete().eq("id", biz_id).execute()
    else:
        db = _get_sqlite()
        db.execute("DELETE FROM businesses WHERE id = ?", (biz_id,))
        db.commit()


# --- Services (shared) ---

def list_services(user_id: str = "") -> list[dict]:
    if USE_SUPABASE:
        res = _get_supabase().table("services").select("*").order("name").execute()
        return res.data or []
    else:
        return [dict(r) for r in _get_sqlite().execute("SELECT * FROM services ORDER BY name").fetchall()]


def get_service(user_id: str, svc_id: str) -> dict | None:
    if USE_SUPABASE:
        res = _get_supabase().table("services").select("*").eq("id", svc_id).execute()
        return res.data[0] if res.data else None
    else:
        row = _get_sqlite().execute("SELECT * FROM services WHERE id = ?", (svc_id,)).fetchone()
        return dict(row) if row else None


def save_service(user_id: str, svc_id: str | None, **fields) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        if svc_id:
            sb.table("services").update(fields).eq("id", svc_id).execute()
        else:
            svc_id = new_id()
            fields.update({"id": svc_id, "user_id": user_id, "created_at": now_iso()})
            sb.table("services").insert(fields).execute()
    else:
        db = _get_sqlite()
        if svc_id:
            sets = ", ".join(f"{k}=?" for k in fields)
            db.execute(f"UPDATE services SET {sets} WHERE id=?", (*fields.values(), svc_id))
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
    if USE_SUPABASE:
        _get_supabase().table("services").delete().eq("id", svc_id).execute()
    else:
        db = _get_sqlite()
        db.execute("DELETE FROM services WHERE id = ?", (svc_id,))
        db.commit()


# --- Results (user-scoped) ---

def save_result(user_id: str, business_id: str, filename: str, deal_json: str, result_json: str) -> str:
    rid = new_id()
    if USE_SUPABASE:
        _get_supabase().table("results").insert({
            "id": rid, "user_id": user_id, "business_id": business_id,
            "filename": filename, "deal_json": json.loads(deal_json), "result_json": json.loads(result_json),
            "note": "", "created_at": now_iso(),
        }).execute()
    else:
        db = _get_sqlite()
        db.execute("INSERT INTO results (id, user_id, business_id, filename, deal_json, result_json, created_at) VALUES (?,?,?,?,?,?,?)",
                   (rid, user_id, business_id, filename, deal_json, result_json, now_iso()))
        db.commit()
    return rid


def list_results(user_id: str, search: str = "", currency: str = "") -> list[dict]:
    if USE_SUPABASE:
        res = _get_supabase().table("results").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        rows = res.data or []
    else:
        rows = [dict(r) for r in _get_sqlite().execute(
            "SELECT * FROM results WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()]

    results = []
    search_lower = search.lower()
    for row in rows:
        try:
            deal = row["deal_json"] if isinstance(row["deal_json"], dict) else json.loads(row["deal_json"])
            result = row["result_json"] if isinstance(row["result_json"], dict) else json.loads(row["result_json"])
            url = deal.get("business_url", "")
            service = deal.get("service_description", "")[:80]
            cur = result.get("currency", "USD")
            if search_lower and search_lower not in url.lower() and search_lower not in service.lower():
                continue
            if currency and cur != currency:
                continue
            results.append({
                "filename": row["filename"], "timestamp": row["created_at"],
                "url": url, "service": service,
                "floor": result.get("price_floor", 0), "target": result.get("price_target", 0),
                "stretch": result.get("price_stretch", 0), "currency": cur,
                "valid": result.get("validation", {}).get("is_valid") if result.get("validation") else None,
                "note": row.get("note", "") or "",
            })
        except Exception:
            continue
    return results


def get_result(user_id: str, filename: str) -> dict | None:
    if USE_SUPABASE:
        res = _get_supabase().table("results").select("*").eq("filename", filename).eq("user_id", user_id).execute()
        if not res.data:
            return None
        row = res.data[0]
        # Ensure JSON fields are strings for compatibility
        if isinstance(row.get("deal_json"), dict):
            row["deal_json"] = json.dumps(row["deal_json"])
        if isinstance(row.get("result_json"), dict):
            row["result_json"] = json.dumps(row["result_json"])
        return row
    else:
        row = _get_sqlite().execute("SELECT * FROM results WHERE filename = ? AND user_id = ?", (filename, user_id)).fetchone()
        return dict(row) if row else None


def add_note_to_result(user_id: str, filename: str, note: str):
    if USE_SUPABASE:
        _get_supabase().table("results").update({"note": note}).eq("filename", filename).eq("user_id", user_id).execute()
    else:
        db = _get_sqlite()
        db.execute("UPDATE results SET note = ? WHERE filename = ? AND user_id = ?", (note, filename, user_id))
        db.commit()


def get_business_results(user_id: str, business_id: str) -> list[dict]:
    if USE_SUPABASE:
        res = _get_supabase().table("results").select("*").eq("user_id", user_id).eq("business_id", business_id).order("created_at", desc=True).execute()
        rows = res.data or []
    else:
        rows = [dict(r) for r in _get_sqlite().execute(
            "SELECT * FROM results WHERE user_id = ? AND business_id = ? ORDER BY created_at DESC",
            (user_id, business_id)).fetchall()]

    results = []
    for row in rows:
        try:
            deal = row["deal_json"] if isinstance(row["deal_json"], dict) else json.loads(row["deal_json"])
            result = row["result_json"] if isinstance(row["result_json"], dict) else json.loads(row["result_json"])
            results.append({"filename": row["filename"], "timestamp": row["created_at"], "deal": deal, "result": result, "note": row.get("note", "") or ""})
        except Exception:
            continue
    return results


def dashboard_stats(user_id: str) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        biz_count = len((sb.table("businesses").select("id").execute()).data or [])
        svc_count = len((sb.table("services").select("id").execute()).data or [])
        res_rows = (sb.table("results").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(5).execute()).data or []
        run_count = len((sb.table("results").select("id").eq("user_id", user_id).execute()).data or [])
    else:
        db = _get_sqlite()
        biz_count = db.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]
        svc_count = db.execute("SELECT COUNT(*) FROM services").fetchone()[0]
        run_count = db.execute("SELECT COUNT(*) FROM results WHERE user_id = ?", (user_id,)).fetchone()[0]
        res_rows = [dict(r) for r in db.execute("SELECT * FROM results WHERE user_id = ? ORDER BY created_at DESC LIMIT 5", (user_id,)).fetchall()]

    recent = []
    targets = []
    for row in res_rows:
        try:
            result = row["result_json"] if isinstance(row["result_json"], dict) else json.loads(row["result_json"])
            deal = row["deal_json"] if isinstance(row["deal_json"], dict) else json.loads(row["deal_json"])
            t = result.get("price_target", 0)
            targets.append(t)
            recent.append({
                "filename": row["filename"], "timestamp": str(row["created_at"])[:10],
                "url": deal.get("business_url", ""), "service": deal.get("service_description", "")[:60],
                "target": t, "currency": result.get("currency", "USD"),
                "valid": result.get("validation", {}).get("is_valid") if result.get("validation") else None,
                "note": row.get("note", "") or "",
            })
        except Exception:
            continue

    return {
        "total_businesses": biz_count, "total_services": svc_count,
        "total_runs": run_count, "avg_target": sum(targets) / len(targets) if targets else 0,
        "recent": recent,
    }


# --- Feedback ---

def save_feedback(user_id: str, user_email: str, page_url: str, category: str, message: str) -> str:
    fid = new_id()
    if USE_SUPABASE:
        _get_supabase().table("feedback").insert({
            "id": fid, "user_id": user_id, "user_email": user_email,
            "page_url": page_url, "category": category, "message": message,
            "status": "open", "created_at": now_iso(),
        }).execute()
    else:
        db = _get_sqlite()
        db.execute("INSERT INTO feedback (id, user_id, user_email, page_url, category, message, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
                   (fid, user_id, user_email, page_url, category, message, "open", now_iso()))
        db.commit()
    return fid


def list_feedback() -> list[dict]:
    if USE_SUPABASE:
        res = _get_supabase().table("feedback").select("*").order("created_at", desc=True).execute()
        return res.data or []
    else:
        return [dict(r) for r in _get_sqlite().execute("SELECT * FROM feedback ORDER BY created_at DESC").fetchall()]
