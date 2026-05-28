from __future__ import annotations

import random
import time
from datetime import datetime
from multiprocessing import Queue


LEVEL_WEIGHTS = {
    "INFO": 0.60,
    "WARNING": 0.25,
    "ERROR": 0.12,
    "CRITICAL": 0.03,
}

LEVEL_MESSAGES = {
    "INFO": [
        "Request processed successfully",
        "Background job completed",
        "Cache refreshed for active session",
        "Heartbeat received from web node",
        "Disk cleanup finished without issues",
    ],
    "WARNING": [
        "CPU usage exceeded 80%",
        "Memory usage trending upward",
        "Retrying connection to analytics service",
        "Response time is above normal threshold",
        "Queue depth is approaching limit",
    ],
    "ERROR": [
        "Database connection timeout",
        "Failed to persist audit record",
        "Authentication service returned 500",
        "Message broker publish operation failed",
        "API gateway could not reach backend",
    ],
    "CRITICAL": [
        "Service unavailable - restart required",
        "Primary database node unreachable",
        "Repeated authentication failures detected",
        "Network partition suspected between nodes",
        "Kernel-level fault reported by host monitor",
    ],
}


def _build_log_line(level: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = random.choice(LEVEL_MESSAGES[level])
    return f"[{timestamp}] {level} {message}"


def run_log_generator(
    output_queue: Queue,
    interval_range: tuple[float, float] = (0.35, 1.10),
) -> None:
    levels = list(LEVEL_WEIGHTS.keys())
    weights = list(LEVEL_WEIGHTS.values())

    while True:
        level = random.choices(levels, weights=weights, k=1)[0]
        output_queue.put(_build_log_line(level))
        time.sleep(random.uniform(*interval_range))
