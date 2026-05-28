from __future__ import annotations

import json
import random
import re
import time
from pathlib import Path


DEFAULT_PARAMS = {
    "delay": 1.0,
    "drop_rate": 20,
    "corruption_rate": 10,
}

CORRUPTION_SYMBOLS = ["?", "#", "*", "!"]
LEVEL_TOKEN_PATTERN = re.compile(r"^\[(?P<timestamp>.*?)\]\s+(?P<level>\S+)\s+(?P<message>.*)$")


def ensure_params_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_PARAMS, indent=2), encoding="utf-8")


def load_params(path: Path) -> dict:
    ensure_params_file(path)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        data = {}

    merged = {**DEFAULT_PARAMS, **data}
    merged["delay"] = max(0.0, float(merged.get("delay", DEFAULT_PARAMS["delay"])))
    merged["drop_rate"] = min(100.0, max(0.0, float(merged.get("drop_rate", DEFAULT_PARAMS["drop_rate"]))))
    merged["corruption_rate"] = min(
        100.0,
        max(0.0, float(merged.get("corruption_rate", DEFAULT_PARAMS["corruption_rate"]))),
    )
    return merged


def save_params(path: Path, params: dict) -> None:
    merged = {**DEFAULT_PARAMS, **params}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(merged, indent=2), encoding="utf-8")


def _corrupt_text_fragment(text: str, *, max_replacements: int) -> str:
    characters = list(text)
    valid_positions = [idx for idx, char in enumerate(characters) if char not in {" ", "\t"}]

    if not valid_positions:
        return text

    replacement_count = min(len(valid_positions), max(1, max_replacements))
    sampled_positions = random.sample(valid_positions, k=replacement_count)

    for index in sampled_positions:
        characters[index] = random.choice(CORRUPTION_SYMBOLS)

    return "".join(characters)


def _corrupt_log_line(log_line: str) -> str:
    match = LEVEL_TOKEN_PATTERN.match(log_line)
    if not match:
        return _corrupt_text_fragment(log_line, max_replacements=max(1, len(log_line) // 8))

    timestamp = match.group("timestamp")
    level = match.group("level")
    message = match.group("message")

    # Corrupt the level token first so the recovery module has something meaningful to repair.
    corrupted_level = _corrupt_text_fragment(level, max_replacements=max(1, len(level) // 2))

    # Optionally add light corruption to the message while preserving the overall log structure.
    if message and random.random() < 0.55:
        corrupted_message = _corrupt_text_fragment(message, max_replacements=max(1, len(message) // 14))
    else:
        corrupted_message = message

    return f"[{timestamp}] {corrupted_level} {corrupted_message}"


class NetworkConstraintSimulator:
    def transmit(self, log_line: str, params: dict) -> dict:
        delay = max(0.0, float(params.get("delay", DEFAULT_PARAMS["delay"])))
        drop_rate = float(params.get("drop_rate", DEFAULT_PARAMS["drop_rate"])) / 100.0
        corruption_rate = float(params.get("corruption_rate", DEFAULT_PARAMS["corruption_rate"])) / 100.0

        if delay > 0:
            low = max(0.0, delay * 0.5)
            high = max(low, delay * 1.5)
            time.sleep(random.uniform(low, high))

        if random.random() < drop_rate:
            return {
                "line": None,
                "dropped": True,
                "corrupted": False,
            }

        if random.random() < corruption_rate:
            return {
                "line": _corrupt_log_line(log_line),
                "dropped": False,
                "corrupted": True,
            }

        return {
            "line": log_line,
            "dropped": False,
            "corrupted": False,
        }
