import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/wishlist.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'available',
            reserved_by TEXT
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gift_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (gift_id) REFERENCES wishlist(id)
        )
        """)

        conn.commit()

def add_item(title: str, description: str | None, username: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO wishlist (title, description, reserved_by) VALUES (?, ?, ?)",
            (title, description, username)
        )
        conn.commit()

        assert cur.lastrowid is not None
        return cur.lastrowid

def delete_gift(gift_id: int, username: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM wishlist WHERE id = ?",
            (gift_id,)
        )
        conn.commit()

def get_all_items():
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT * FROM wishlist ORDER BY id"
        )
        return cur.fetchall()


def add_comment(gift_id: int, author: str, text: str):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO comments (gift_id, author, text, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (gift_id, author, text, datetime.utcnow().isoformat())
        )

        conn.execute(
            "UPDATE wishlist SET status = 'commented' WHERE id = ? AND status != 'reserved'",
            (gift_id,)
        )

        conn.commit()


def get_comments_for_gift(gift_id: int):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            """
            SELECT author, text
            FROM comments
            WHERE gift_id = ?
            ORDER BY id
            """,
            (gift_id,)
        )
        return cur.fetchall()

def get_reserved_by(gift_id: int):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            """
            SELECT reserved_by
            FROM wishlist
            WHERE id = ?
            ORDER BY id
            """,
            (gift_id,)
        )
        return cur.fetchone()

def reserve_gift(gift_id: int, user: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE wishlist SET status = 'reserved', reserved_by = ? WHERE id = ?",
            (user, gift_id)
        )
        conn.commit()


def unreserve_gift(gift_id: int):
    comments_rows = get_comments_for_gift(gift_id)
    status = 'commented' if comments_rows else 'available'
    with get_connection() as conn:
        conn.execute(
            "UPDATE wishlist SET status = ?, reserved_by = NULL WHERE id = ?",
            (status, gift_id)
        )
        conn.commit()


def delete_comment(comment_id: int, author: str):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM comments WHERE id = ? AND author = ?",
            (comment_id, author)
        )
        conn.commit()


def update_comment(comment_id: int, author: str, text: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE comments SET text = ? WHERE id = ? AND author = ?",
            (text, comment_id, author)
        )
        conn.commit()
