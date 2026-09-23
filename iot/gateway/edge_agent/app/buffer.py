import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional



class SQLiteBuffer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._ensure_storage_dir()
        self.init_db()

    def _ensure_storage_dir(self) -> None:
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS telemetry_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        node_id TEXT NOT NULL,
                        sequence INTEGER NOT NULL,
                        timestamp TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        received_at TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'PENDING',
                        retry_count INTEGER NOT NULL DEFAULT 0,
                        last_attempt_at TEXT,
                        CONSTRAINT uq_node_sequence UNIQUE (node_id, sequence)
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS ix_queue_status_id ON telemetry_queue (status, id)"
                )
                conn.commit()

    def enqueue(self, telemetry_dict: Dict[str, Any]) -> Tuple[bool, bool, Optional[int]]:
        """
        Enqueues a canonical telemetry packet into the persistent buffer.
        Returns:
            (is_success, is_duplicate, queue_id)
        """
        node_id = telemetry_dict.get("node_id")
        sequence = telemetry_dict.get("sequence")
        timestamp = telemetry_dict.get("timestamp")
        received_at = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(telemetry_dict)

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """
                        INSERT INTO telemetry_queue 
                            (node_id, sequence, timestamp, payload, received_at, status, retry_count)
                        VALUES (?, ?, ?, ?, ?, 'PENDING', 0)
                        """,
                        (node_id, sequence, timestamp, payload_json, received_at),
                    )
                    conn.commit()
                    return True, False, cursor.lastrowid
                except sqlite3.IntegrityError:
                    # Duplicate (node_id, sequence) detected!
                    cursor.execute(
                        "SELECT id FROM telemetry_queue WHERE node_id = ? AND sequence = ?",
                        (node_id, sequence),
                    )
                    row = cursor.fetchone()
                    existing_id = row["id"] if row else None
                    return True, True, existing_id

    def get_pending(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves oldest pending records in FIFO order for forwarding."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, node_id, sequence, timestamp, payload, retry_count
                    FROM telemetry_queue
                    WHERE status = 'PENDING'
                    ORDER BY id ASC
                    LIMIT ?
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    results.append({
                        "id": row["id"],
                        "node_id": row["node_id"],
                        "sequence": row["sequence"],
                        "timestamp": row["timestamp"],
                        "payload": json.loads(row["payload"]),
                        "retry_count": row["retry_count"],
                    })
                return results

    def mark_sent(self, queue_id: int) -> None:
        """Marks a queued record as successfully delivered."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE telemetry_queue SET status = 'SENT', last_attempt_at = ? WHERE id = ?",
                    (datetime.now(timezone.utc).isoformat(), queue_id),
                )
                conn.commit()

    def mark_failed(self, queue_id: int) -> None:
        """Increments retry count and updates attempt timestamp while remaining PENDING."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    UPDATE telemetry_queue 
                    SET retry_count = retry_count + 1, 
                        last_attempt_at = ?
                    WHERE id = ?
                    """,
                    (datetime.now(timezone.utc).isoformat(), queue_id),
                )
                conn.commit()

    def get_queue_size(self) -> int:
        """Returns the count of currently pending records."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) AS cnt FROM telemetry_queue WHERE status = 'PENDING'")
                row = cursor.fetchone()
                return row["cnt"] if row else 0

    def clear(self) -> None:
        """Clears the table (used in test isolation)."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM telemetry_queue")
                conn.commit()
