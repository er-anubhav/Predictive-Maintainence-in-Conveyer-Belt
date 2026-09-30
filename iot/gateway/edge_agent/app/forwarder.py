import time
import threading
from datetime import datetime, timezone
from typing import Optional
import requests

from app.config import settings
from app.buffer import SQLiteBuffer
from app.metrics import metrics_manager


class ForwardingWorker:
    def __init__(self, buffer: SQLiteBuffer):
        self.buffer = buffer
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.consecutive_failures = 0
        self.last_forwarded_at: Optional[str] = None
        self.is_connected: bool = False

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="GatewayForwarder")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._wake_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def trigger_wake(self) -> None:
        """Signals the worker to wake immediately upon new packet arrival."""
        self._wake_event.set()

    def _run(self) -> None:
        target_url = f"{settings.BACKEND_URL.rstrip('/')}/api/v1/telemetry"

        while not self._stop_event.is_set():
            pending_records = self.buffer.get_pending(limit=settings.BATCH_SIZE)

            if not pending_records:
                # Sleep until next poll interval or until woken up by new packet
                self._wake_event.wait(timeout=settings.POLL_INTERVAL_SECONDS)
                self._wake_event.clear()
                continue

            for record in pending_records:
                if self._stop_event.is_set():
                    break

                queue_id = record["id"]
                payload = record["payload"]

                try:
                    response = requests.post(
                        target_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=settings.BACKEND_TIMEOUT_SECONDS,
                    )

                    if response.status_code in (200, 201):
                        self.buffer.mark_sent(queue_id)
                        metrics_manager.inc_forwarded()
                        self.last_forwarded_at = datetime.now(timezone.utc).isoformat()
                        self.consecutive_failures = 0
                        self.is_connected = True
                    else:
                        # Backend returned 4xx or 5xx
                        self.buffer.mark_failed(queue_id)
                        metrics_manager.inc_failed()
                        self.consecutive_failures += 1
                        self._apply_backoff()
                        break  # Stop this batch and retry after backoff

                except (requests.ConnectionError, requests.Timeout, requests.RequestException):
                    # Central backend is down / unreachable
                    self.buffer.mark_failed(queue_id)
                    metrics_manager.inc_failed()
                    self.consecutive_failures += 1
                    self.is_connected = False
                    self._apply_backoff()
                    break

    def _apply_backoff(self) -> None:
        """Calculates exponential backoff to avoid consuming CPU when backend is offline."""
        backoff_seconds = min(
            settings.MAX_RETRY_BACKOFF_SECONDS,
            1.0 * (2 ** min(self.consecutive_failures, 5)),
        )
        self._wake_event.wait(timeout=backoff_seconds)
        self._wake_event.clear()
