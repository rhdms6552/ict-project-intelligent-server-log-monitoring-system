from __future__ import annotations

import difflib
import re


KNOWN_LEVELS = ["INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_PATTERN = re.compile(r"^\[(?P<timestamp>.*?)\]\s+(?P<level>\S+)\s+(?P<message>.*)$")


def sanitize_level_token(token: str) -> str:
    return re.sub(r"[^A-Za-z]", "", token).upper()


def recover_level_token(token: str) -> tuple[str | None, bool]:
    normalized = sanitize_level_token(token)

    if not normalized:
        return None, False

    if normalized in KNOWN_LEVELS:
        return normalized, normalized != token

    match = difflib.get_close_matches(normalized, KNOWN_LEVELS, n=1, cutoff=0.45)
    if match:
        return match[0], True

    return None, False


def recover_log_line(log_line: str) -> tuple[str, bool]:
    match = LOG_PATTERN.match(log_line)

    if not match:
        return log_line, False

    timestamp = match.group("timestamp")
    level_token = match.group("level")
    message = match.group("message")

    recovered_level, recovered = recover_level_token(level_token)
    if not recovered_level:
        return log_line, False

    rebuilt = f"[{timestamp}] {recovered_level} {message}"
    return rebuilt, recovered
