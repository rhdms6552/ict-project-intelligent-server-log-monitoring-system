from __future__ import annotations

from collections import Counter


def evaluate_window(window_levels: list[str], drop_rate_ratio: float) -> dict:
    counts = Counter(window_levels)
    critical_count = counts.get("CRITICAL", 0)
    error_count = counts.get("ERROR", 0)
    warning_count = counts.get("WARNING", 0)

    if critical_count >= 1:
        status = "CRITICAL"
    elif error_count >= 3:
        status = "WARNING"
    else:
        status = "STABLE"

    anomaly_score = 0.0
    anomaly_score += min(0.25, warning_count * 0.04)
    anomaly_score += min(0.35, error_count * 0.12)
    anomaly_score += min(0.75, critical_count * 0.55)

    if status == "WARNING":
        anomaly_score = max(anomaly_score, 0.55)
    elif status == "CRITICAL":
        anomaly_score = max(anomaly_score, 0.90)

    if drop_rate_ratio >= 0.5:
        anomaly_score += 0.3

    anomaly_score = max(0.0, min(1.0, round(anomaly_score, 2)))

    return {
        "status": status,
        "anomaly_score": anomaly_score,
        "window_counts": dict(counts),
    }
