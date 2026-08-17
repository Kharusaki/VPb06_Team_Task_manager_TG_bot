import sqlite3
from datetime import datetime
from typing import Optional

from bot.config import DATABASE_PATH


class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    user_id INTEGER NOT NULL,
                    username TEXT DEFAULT '',
                    status TEXT DEFAULT 'Не начата',
                    priority TEXT DEFAULT 'Средний',
                    assigned_to INTEGER DEFAULT NULL,
                    assigned_to_name TEXT DEFAULT '',
                    planned_end_date TEXT DEFAULT NULL,
                    completed_at TEXT DEFAULT NULL,
                    closed_by_name TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT DEFAULT '',
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)

    def add_task(
        self,
        title: str,
        description: str,
        user_id: int,
        username: str,
        planned_end_date: Optional[str] = None,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (title, description, user_id, username, planned_end_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    description,
                    user_id,
                    username,
                    planned_end_date,
                    datetime.now().isoformat(),
                ),
            )
            return cursor.lastrowid  # type: ignore

    def get_all_tasks(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
            return [dict(row) for row in rows]

    def get_tasks_by_user(self, user_id: int) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE user_id = ? OR assigned_to = ? ORDER BY id DESC",
                (user_id, user_id),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_task_by_id(self, task_id: int) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def update_task_title(self, task_id: int, title: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("UPDATE tasks SET title = ? WHERE id = ?", (title, task_id))
            return cursor.rowcount > 0

    def update_task_description(self, task_id: int, description: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE tasks SET description = ? WHERE id = ?", (description, task_id)
            )
            return cursor.rowcount > 0

    def update_task_status(self, task_id: int, status: str) -> bool:
        completed_at = None
        closed_by = ""
        if status == "Выполнена":
            completed_at = datetime.now().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
                (status, completed_at, task_id),
            )
            return cursor.rowcount > 0

    def set_completed_by(self, task_id: int, closed_by_name: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE tasks SET closed_by_name = ? WHERE id = ?",
                (closed_by_name, task_id),
            )
            return cursor.rowcount > 0

    def update_task_priority(self, task_id: int, priority: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE tasks SET priority = ? WHERE id = ?", (priority, task_id)
            )
            return cursor.rowcount > 0

    def delegate_task(self, task_id: int, assigned_to: int, assigned_to_name: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE tasks SET assigned_to = ?, assigned_to_name = ? WHERE id = ?",
                (assigned_to, assigned_to_name, task_id),
            )
            return cursor.rowcount > 0

    def update_planned_date(self, task_id: int, planned_end_date: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE tasks SET planned_end_date = ? WHERE id = ?",
                (planned_end_date, task_id),
            )
            return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0

    def add_comment(self, task_id: int, user_id: int, username: str, text: str) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO comments (task_id, user_id, username, text, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (task_id, user_id, username, text, datetime.now().isoformat()),
            )
            return cursor.lastrowid  # type: ignore

    def get_comments_by_task(self, task_id: int) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM comments WHERE task_id = ? ORDER BY id ASC",
                (task_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_comment_count(self, task_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM comments WHERE task_id = ?",
                (task_id,),
            ).fetchone()
            return row["cnt"] if row else 0
