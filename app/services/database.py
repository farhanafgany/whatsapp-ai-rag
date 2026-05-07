import sqlite3
from pathlib import Path

DB_PATH = Path("nexora.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            role         TEXT NOT NULL,
            content      TEXT NOT NULL,
            timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_history(phone_number: str, limit: int = 10) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        """SELECT role, content FROM conversations
           WHERE phone_number = ?
           ORDER BY timestamp DESC LIMIT ?""",
        (phone_number, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in reversed(rows)]


def save_message(phone_number: str, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO conversations (phone_number, role, content) VALUES (?, ?, ?)",
        (phone_number, role, content),
    )
    conn.commit()
    conn.close()


def get_all_users() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        """SELECT phone_number, COUNT(*) as msg_count, MAX(timestamp) as last_active
           FROM conversations
           GROUP BY phone_number
           ORDER BY last_active DESC"""
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"phone_number": r[0], "msg_count": r[1], "last_active": r[2]} for r in rows]


def get_full_history(phone_number: str, limit: int = 200) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        """SELECT role, content, timestamp FROM conversations
           WHERE phone_number = ?
           ORDER BY timestamp ASC LIMIT ?""",
        (phone_number, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]


def delete_history(phone_number: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM conversations WHERE phone_number = ?", (phone_number,))
    conn.commit()
    conn.close()
