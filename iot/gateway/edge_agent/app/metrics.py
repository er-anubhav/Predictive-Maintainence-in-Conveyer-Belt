import threading
from typing import Dict, Any


class MetricsManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.packets_received = 0
        self.packets_queued = 0
        self.packets_forwarded = 0
        self.packets_failed = 0
        self.duplicate_packets = 0

    def inc_received(self) -> None:
        with self._lock:
            self.packets_received += 1

    def inc_queued(self) -> None:
        with self._lock:
            self.packets_queued += 1

    def inc_forwarded(self) -> None:
        with self._lock:
            self.packets_forwarded += 1

    def inc_failed(self) -> None:
        with self._lock:
            self.packets_failed += 1

    def inc_duplicate(self) -> None:
        with self._lock:
            self.duplicate_packets += 1

    def get_metrics(self, current_queue_size: int) -> Dict[str, Any]:
        with self._lock:
            return {
                "packets_received": self.packets_received,
                "packets_queued": self.packets_queued,
                "packets_forwarded": self.packets_forwarded,
                "packets_failed": self.packets_failed,
                "duplicate_packets": self.duplicate_packets,
                "current_queue_size": current_queue_size,
            }

    def reset(self) -> None:
        with self._lock:
            self.packets_received = 0
            self.packets_queued = 0
            self.packets_forwarded = 0
            self.packets_failed = 0
            self.duplicate_packets = 0


metrics_manager = MetricsManager()
