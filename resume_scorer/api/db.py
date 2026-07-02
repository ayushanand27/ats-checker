"""SQLite persistence for user accounts, master profiles, and analysis history.

Self-contained (stdlib sqlite3) so it runs identically locally and on AWS EC2.
Swap DB_PATH / migrate to Postgres later without changing route code.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_DEFAULT_DIR = Path(__file__).resolve().parents[1] / "data"
DB_PATH = Path(os.getenv("RESUMEMATCH_DB", str(_DEFAULT_DIR / "resumematch.db")))

_LOCK = threading.Lock()
_INITIALIZED = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return
    with _LOCK:
        if _INITIALIZED:
            return
        conn = get_conn()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS profiles (
                    user_id INTEGER PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    jd_title TEXT,
                    jd_text TEXT,
                    core_score REAL,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_analyses_user
                    ON analyses(user_id, created_at DESC);
                """
            )
            conn.commit()
        finally:
            conn.close()
        _INITIALIZED = True


# ----- users -----

def create_user(email: str, password_hash: str, name: Optional[str]) -> dict[str, Any]:
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, name, created_at) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), password_hash, name, _now()),
        )
        conn.commit()
        return get_user_by_id(cur.lastrowid)  # type: ignore[arg-type]
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[dict[str, Any]]:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[dict[str, Any]]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ----- profiles -----

def upsert_profile(user_id: int, profile: dict[str, Any]) -> None:
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO profiles (user_id, profile_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                profile_json = excluded.profile_json,
                updated_at = excluded.updated_at
            """,
            (user_id, json.dumps(profile), _now()),
        )
        conn.commit()
    finally:
        conn.close()


def get_profile(user_id: int) -> Optional[dict[str, Any]]:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT profile_json, updated_at FROM profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "profile": json.loads(row["profile_json"]),
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


# ----- analyses (history) -----

def save_analysis(
    user_id: int,
    jd_title: Optional[str],
    jd_text: Optional[str],
    core_score: Optional[float],
    result: dict[str, Any],
) -> int:
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO analyses (user_id, jd_title, jd_text, core_score, result_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, jd_title, jd_text, core_score, json.dumps(result), _now()),
        )
        conn.commit()
        return int(cur.lastrowid)  # type: ignore[arg-type]
    finally:
        conn.close()


def list_analyses(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, jd_title, core_score, created_at
            FROM analyses WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_analysis(user_id: int, analysis_id: int) -> Optional[dict[str, Any]]:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user_id),
        ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["result"] = json.loads(data.pop("result_json"))
        return data
    finally:
        conn.close()


def delete_analysis(user_id: int, analysis_id: int) -> bool:
    conn = get_conn()
    try:
        cur = conn.execute(
            "DELETE FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
