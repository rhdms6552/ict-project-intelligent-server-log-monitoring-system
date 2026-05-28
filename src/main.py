from __future__ import annotations

import json
import multiprocessing as mp
import time
from pathlib import Path
from queue import Empty

from ai_recovery import recover_log_line
from decision_engine import evaluate_window
from log_generator import run_log_generator
from log_processor import LogProcessor
from network_constraint import NetworkConstraintSimulator, ensure_params_file, load_params


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATE_PATH = DATA_DIR / "state.json"
PARAMS_PATH = DATA_DIR / "params.json"


def _write_state(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _initial_state(params: dict) -> dict:
    return {
        "status": "WAITING",
        "anomaly_score": 0.0,
        "counts": {
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
        },
        "stats": {
            "total_received": 0,
            "total_dropped": 0,
            "total_corrupted": 0,
            "total_recovered": 0,
            "drop_rate": 0.0,
        },
        "params": params,
        "recent_logs": [],
        "error_rate_history": [],
        "window_size": 0,
        "last_updated": "",
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ensure_params_file(PARAMS_PATH)
    params = load_params(PARAMS_PATH)
    _write_state(_initial_state(params))

    log_queue: mp.Queue = mp.Queue()
    generator_process = mp.Process(target=run_log_generator, args=(log_queue,), daemon=True)
    generator_process.start()

    simulator = NetworkConstraintSimulator()
    processor = LogProcessor()
    last_status_print = 0.0

    try:
        while True:
            params = load_params(PARAMS_PATH)

            try:
                raw_log = log_queue.get(timeout=0.5)
            except Empty:
                decision = evaluate_window(processor.current_window_levels(), processor.drop_rate_ratio)
                _write_state(processor.build_state(decision, params))
                continue

            transmission = simulator.transmit(raw_log, params)

            if transmission["dropped"]:
                processor.record_drop(raw_log)
            else:
                transmitted_line = transmission["line"]
                recovered_line, recovered = recover_log_line(transmitted_line)
                processor.process_log(
                    recovered_line,
                    corrupted=transmission["corrupted"],
                    recovered=recovered,
                    original_line=transmitted_line,
                )

            decision = evaluate_window(processor.current_window_levels(), processor.drop_rate_ratio)
            state = processor.build_state(decision, params)
            _write_state(state)

            now = time.time()
            if now - last_status_print >= 3:
                print(
                    f"[STATUS] {state['status']} | "
                    f"Score={state['anomaly_score']:.2f} | "
                    f"Received={state['stats']['total_received']} | "
                    f"Dropped={state['stats']['total_dropped']} | "
                    f"Recovered={state['stats']['total_recovered']}"
                )
                last_status_print = now
    except KeyboardInterrupt:
        print("\nShutting down log monitoring pipeline...")
    finally:
        if generator_process.is_alive():
            generator_process.terminate()
            generator_process.join(timeout=2)


if __name__ == "__main__":
    mp.freeze_support()
    main()
