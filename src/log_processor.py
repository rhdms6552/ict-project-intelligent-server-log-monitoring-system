from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from typing import Any


def _extract_timestamp(log_line: str) -> str:
    if log_line.startswith("[") and "]" in log_line:
        return log_line[1 : log_line.index("]")]
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _extract_level(log_line: str) -> str:
    if "]" not in log_line:
        return "INFO"

    tail = log_line.split("]", 1)[1].strip()
    if not tail:
        return "INFO"

    return tail.split(" ", 1)[0].upper()


class LogProcessor:
    def __init__(self) -> None:
        self.window = deque(maxlen=20)
        self.log_history = deque(maxlen=200)
        self.error_window = deque()
        self.error_rate_series = deque(maxlen=120)
        self.counts = {
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
        }
        self.stats = {
            "total_received": 0,
            "total_dropped": 0,
            "total_corrupted": 0,
            "total_recovered": 0,
        }

    @property
    def drop_rate_ratio(self) -> float:
        total_events = self.stats["total_received"] + self.stats["total_dropped"]
        if total_events == 0:
            return 0.0
        return self.stats["total_dropped"] / total_events

    def _trim_error_window(self) -> None:
        cutoff = datetime.now() - timedelta(seconds=60)
        while self.error_window and self.error_window[0]["time"] < cutoff:
            self.error_window.popleft()

    def _record_error_rate(self, level: str | None) -> None:
        now = datetime.now()
        self.error_window.append(
            {
                "time": now,
                "is_error": level in {"ERROR", "CRITICAL"},
                "is_counted": level is not None,
            }
        )
        self._trim_error_window()

        counted = [item for item in self.error_window if item["is_counted"]]
        if counted:
            error_rate = sum(1 for item in counted if item["is_error"]) / len(counted)
        else:
            error_rate = 0.0

        self.error_rate_series.append(
            {
                "timestamp": now.strftime("%H:%M:%S"),
                "error_rate": round(error_rate, 3),
            }
        )

    def record_drop(self, raw_log: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.stats["total_dropped"] += 1
        self.log_history.append(
            {
                "timestamp": timestamp,
                "level": "DROPPED",
                "display": f"Dropped before delivery | {raw_log}",
                "recovered": False,
                "corrupted": False,
                "dropped": True,
            }
        )
        self._record_error_rate(None)

    def process_log(
        self,
        log_line: str,
        *,
        corrupted: bool = False,
        recovered: bool = False,
        original_line: str | None = None,
    ) -> None:
        level = _extract_level(log_line)
        timestamp = _extract_timestamp(log_line)

        self.stats["total_received"] += 1
        if corrupted:
            self.stats["total_corrupted"] += 1
        if recovered:
            self.stats["total_recovered"] += 1

        if level not in self.counts:
            level = "INFO"

        self.counts[level] += 1
        self.window.append(level)
        self.log_history.append(
            {
                "timestamp": timestamp,
                "level": level,
                "display": log_line,
                "recovered": recovered,
                "corrupted": corrupted,
                "dropped": False,
                "original": original_line,
            }
        )
        self._record_error_rate(level)

    def build_state(self, decision: dict, params: dict) -> dict[str, Any]:
        self._trim_error_window()
        return {
            "status": decision["status"],
            "anomaly_score": decision["anomaly_score"],
            "counts": self.counts,
            "stats": {
                **self.stats,
                "drop_rate": round(self.drop_rate_ratio * 100, 1),
            },
            "params": params,
            "recent_logs": list(self.log_history),
            "error_rate_history": list(self.error_rate_series),
            "window_size": len(self.window),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def current_window_levels(self) -> list[str]:
        return list(self.window)
