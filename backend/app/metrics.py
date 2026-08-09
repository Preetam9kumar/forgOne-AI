from __future__ import annotations

import time
from threading import Lock


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self.start_time = time.time()
        self.request_count = 0
        self.success_count = 0
        self.client_error_count = 0
        self.server_error_count = 0
        self.total_response_time_s = 0.0

    def record_request(self, status_code: int, response_time_s: float) -> None:
        with self._lock:
            self.request_count += 1
            self.total_response_time_s += response_time_s
            if 200 <= status_code < 300:
                self.success_count += 1
            elif 400 <= status_code < 500:
                self.client_error_count += 1
            elif status_code >= 500:
                self.server_error_count += 1

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            average_response_ms = (
                self.total_response_time_s / self.request_count * 1000.0
                if self.request_count
                else 0.0
            )
            return {
                "uptime_seconds": round(time.time() - self.start_time, 2),
                "request_count": self.request_count,
                "success_count": self.success_count,
                "client_error_count": self.client_error_count,
                "server_error_count": self.server_error_count,
                "average_response_time_ms": round(average_response_ms, 2),
            }


metrics = Metrics()
