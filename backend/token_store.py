import os
import sqlite3
import threading

_lock = threading.Lock()


def _db_path() -> str:
    return os.getenv("TOKEN_DB_PATH", "tokens.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), check_same_thread=False)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tokens "
        "(user_id TEXT PRIMARY KEY, encrypted_token BLOB NOT NULL)"
    )
    conn.commit()
    return conn


_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = _connect()
    return _conn


def save_token(user_id: str, encrypted_token: bytes) -> None:
    with _lock:
        _get_conn().execute(
            "INSERT OR REPLACE INTO tokens (user_id, encrypted_token) VALUES (?, ?)",
            (user_id, encrypted_token),
        )
        _get_conn().commit()


def get_token(user_id: str) -> bytes | None:
    with _lock:
        row = _get_conn().execute(
            "SELECT encrypted_token FROM tokens WHERE user_id = ?", (user_id,)
        ).fetchone()
    return bytes(row[0]) if row else None


def delete_token(user_id: str) -> None:
    with _lock:
        _get_conn().execute("DELETE FROM tokens WHERE user_id = ?", (user_id,))
        _get_conn().commit()
